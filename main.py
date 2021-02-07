from argparse import ArgumentParser
import cv2
from functools import partial
import io
import json
from pathlib import Path
import telebot
import traceback
import sys

from command import Command
from logger import Logger
from message import MessageType, ImageData, TextData
from processor import Processor


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', help='path to a config file', type=Path)
    parser.add_argument('-l', '--logpath', help='path to a directory with log files', type=Path)
    return parser.parse_args()


class Bot:
    def __init__(self, token, processor, logpath):
        self._logger = Logger(logpath)
        self._construct_default_commands()
        self._join_commands(processor)
        self.bot = telebot.TeleBot(token)
        del token

        @self.bot.message_handler(content_types=['text'])
        def get_text_message(message):
            self._logger.log_message(message.chat.username, message.text)
            cmd = self._CMD[MessageType.TEXT].get(message.text, self._process_unknown)
            input_data = TextData(message.text)
            try:
                result = cmd(input_data)
                self._return_data(message.from_user.id, result)
            except Exception as err:
                exc_info = sys.exc_info()
                exc = traceback.format_exception(*exc_info)
                self._logger.log_message(message.chat.username, ''.join(exc))

        self.bot.polling(none_stop=True, interval=0)

    def _construct_default_commands(self):
        self._CMD = {t: {} for t in MessageType}
        self._CMD[MessageType.TEXT]['/stat'] = Command('Prints usage statistics', self._get_stat)
        self._CMD[MessageType.TEXT]['/help'] = Command('Prints help message', self._print_help)

    def _join_commands(self, processor):
        processor_cmds = processor.get_commands()
        for cmd_type, cmds in processor_cmds.items():
            # check duplicate
            common_cmds = set(self._CMD[cmd_type].keys()).intersection(set(cmds.keys()))
            assert len(common_cmds) == 0, f"Processor shouldn't contain commands {common_cmds} of type {cmd_type}"
            # merge commands
            self._CMD[cmd_type].update(cmds)


    def _print_help(self, message):
        commands = []
        for name, command in self._CMD[MessageType.TEXT].items():
            commands.append(f'{name}: {command}')
        return TextData('\n'.join(commands))


    def _get_stat(self, message):
        stat = self._logger.get_stat()
        stat = '\n'.join(stat.split('\n')[-10:])
        return TextData(stat)


    def _process_unknown(self, message):
        return TextData('Unknow command.\n/help to get availabe commands')


    def _return_data(self, user_id, data):
        if data is None:
            return
        if isinstance(data, TextData):
            self.bot.send_message(user_id, data._message_data)
        elif isinstance(data, ImageData):
            buf = io.BytesIO()
            buf.write(bytes(cv2.imencode('.jpg', data._message_data)[1]))
            buf.seek(0)
            self.bot.send_photo(user_id, buf)
            del buf
        else:
            assert False, f'unsupported data type {type(data)}'

if __name__=='__main__':
    args = parse_args()
    config = json.loads(args.config.read_text())
    args.config.unlink()
    args.__dict__.pop('config')
    processor = Processor(config['camera_id'])
    Bot(config.pop('token', None), processor, args.logpath)
