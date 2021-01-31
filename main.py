import telebot
import json
from pathlib import Path
import sys
import cv2
import traceback
import io
from argparse import ArgumentParser
import logging
import re

from cam_holder import CamHolder
from singleton_processor import SingletonProcessor
from detector import YOLODetector


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

def get_stat(bot, message, logger, processor, cam):
    if message.chat.username != 'eshalnov':
        process_unknown(bot, message)
    stat = args.logger.get_stat()
    stat = stat.split('\n')
    N = 10
    for i in range(0, len(stat), N):
        bot.send_message(message.from_user.id, '\n'.join(stat[i:i+N]))

def process_unknown(bot, message):
    bot.send_message(message.from_user.id, 'Unknow command.\n/help to get availabe commands')

def main(args, config):
    CMD = {'/start': process,
           '/stat': get_stat,
           '/help': print_help}
    cam = CamHolder(config['camera_id'])
    processor = SingletonProcessor(YOLODetector)

    bot = telebot.TeleBot(config.pop('token', None))

    @bot.message_handler(content_types=['text'])
    def get_text_message(message):
        args.logger.log_message(message.chat.username, message.text)
        cmd = CMD.get(message.text, process_unknown)
        args.logger.log_message('', cmd)
        try:
            cmd(bot, message, args.logger, processor, cam)
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
    main(args, config)
