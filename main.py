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


def print_help(message):
    pass


def get_stat(message, logger):
    stat = logger.get_stat()
    stat = '\n'.join(stat.split('\n')[-10:])
    return TextData(stat)


def process_unknown(message):
    return TextData('Unknow command.\n/help to get availabe commands')


def return_data(bot, user_id, data):
    if data is None:
        return
    if isinstance(data, TextData):
        bot.send_message(user_id, data._message_data)
    elif isinstance(data, ImageData):
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
