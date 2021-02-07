from argparse import ArgumentParser
import cv2
from enum import Enum
from functools import partial
import io
import json
import logging
from pathlib import Path
import re
import telebot
import traceback
import sys

from cam_holder import CamHolder
from detector import YOLODetector
from singleton_processor import SingletonProcessor


class MessageType(Enum):
    TEXT=0
    IMAGE=1
    FILE=2
    VIDEO=3

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', help='path to a config file', type=Path)
    parser.add_argument('-l', '--logpath', help='path to a directory with log files', type=Path)
    return parser.parse_args()

class Logger():
    def __init__(self, args):
        self.log_path = args.logpath
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.template = re.compile(r'log(\d+).log')
        index = max(self.get_existing_indices() + [-1]) + 1
        self.logfile = self.log_path/f'log{index}.log'

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(format='%(asctime)-15s %(message)s', filename=self.logfile, level=logging.INFO)

    def _get_existing_info(self):
        files = list(self.log_path.glob(r'log*.log'))
        match = [(x, self.template.match(x.name)) for x in files]
        return {int(x[1].groups()[0][0]): x[0] for x in match if not x[1] is None}

    def get_existing_files(self):
        info = self._get_existing_info()
        return [info[k] for k in sorted(info.keys())]

    def get_existing_indices(self):
        return list(self._get_existing_info().keys())

    def log_message(self, user, text):
        self.logger.info(f'{user}: {text}')

    def get_stat(self):
        return ''.join([f.read_text() for f in self.get_existing_files() if f != self.logfile])


def print_help(bot, message, logger, processor, cam):
    bot.send_message(message.from_user.id, '/start to get data')

def process(bot, message, logger, processor, cam):
    img = cam.get_image()
    img = processor(img)
    buf = io.BytesIO()
    buf.write(bytes(cv2.imencode('.jpg', img)[1]))
    buf.seek(0)
    bot.send_photo(message.from_user.id, buf)
    del buf

def get_stat(message, logger):
    stat = logger.get_stat()
    stat = '\n'.join(stat.split('\n')[-10:])
    return TextData(stat)

def process_unknown(message):
    return TextData('Unknow command.\n/help to get availabe commands')

class Data:
    def __init__(self, message_type, message_data):
        self._message_type = message_type
        self._message_data = message_data

    def get_type(self):
        return self._message_type

class TextData(Data):
    def __init__(self, text):
        super().__init__(MessageType.TEXT, text)

class ImageData(Data):
    def __init__(self, img):
        super().__init__(MessageType.IMAGE, img)

class Command:
    def __init__(self, description, processor):
        self._description = description
        self._processor = processor

    def __call__(self, *args, **kwargs):
        return self._processor(*args, **kwargs)

    def __str__(self):
        return self._description + f' {self._processor}'


class Processor:
    def __init__(self, camera_id):
        self._cam = CamHolder(camera_id)
        self._processor = SingletonProcessor(YOLODetector)
        pass

    def get_commands(self):
        return {MessageType.TEXT: {'/start': Command(description='Returns image from a camera', processor=self.__call__)}}

    def __call__(self, data):
        assert data._message_type == MessageType.TEXT and data._message_data == '/start'
        img = self._cam.get_image()
        img = self._processor(img)
        return ImageData(img)

def return_data(bot, user_id, data):
    if isinstance(data, TextData):
        bot.send_message(user_id, data._message_data)
    if isinstance(data, ImageData):
        buf = io.BytesIO()
        buf.write(bytes(cv2.imencode('.jpg', data._message_data)[1]))
        buf.seek(0)
        bot.send_photo(user_id, buf)
        del buf
    else:
        assert False, f'unsupported data type {type(data)}'

def main(args, token, processor):
    CMD = {MessageType.TEXT: {'/stat': Command('Prints usage statistics', partial(get_stat, logger=args.logger)),
                              '/help': Command('Prints help message', print_help)},
           MessageType.IMAGE: {},
           MessageType.VIDEO: {},
           MessageType.FILE: {}}
    processor_cmds = processor.get_commands()
    for cmd_type in MessageType:
        # check duplicate
        if cmd_type in processor_cmds and cmd_type in CMD:
            common_cmds = set(CMD[cmd_type].keys()).intersection(set(processor_cmds[cmd_type].keys()))
            assert len(common_cmds) == 0, f"Processor shouldn't contain commands {common_cmds} of type {cmd_type}"
        # merge commands
        if cmd_type not in CMD:
            CMD[cmd_type] = {}
        if cmd_type not in processor_cmds:
            processor_cmds[cmd_type] = {}
        CMD[cmd_type].update(processor_cmds[cmd_type])

    bot = telebot.TeleBot(token)
    del token

    @bot.message_handler(content_types=['text'])
    def get_text_message(message):
        args.logger.log_message(message.chat.username, message.text)
        cmd = CMD[MessageType.TEXT].get(message.text, process_unknown)
        args.logger.log_message('', cmd)
        input_data = TextData(message.text)
        try:
            result = cmd(input_data)
            return_data(bot, message.from_user.id, result)
        except Exception as err:
            exc_info = sys.exc_info()
            exc = traceback.format_exception(*exc_info)
            args.logger.log_message('', ''.join(exc))

    bot.polling(none_stop=True, interval=0)

if __name__=='__main__':
    args = parse_args()
    args.logger = Logger(args)
    config = json.loads(args.config.read_text())
    args.config.unlink()
    args.__dict__.pop('config')
    processor = Processor(config['camera_id'])
    main(args, config.pop('token', None), processor)
