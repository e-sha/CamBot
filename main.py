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


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', help='path to a config file', type=Path)
    parser.add_argument('-l', '--logpath', help='path to a directory with log files', type=Path)
    return parser.parse_args()

class LogRotator():
    def __init__(self, args):
        self.log_path = args.logpath
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.template = re.compile(r'log(\d+).log')
        print(self.get_existing_indices())
        index = max(self.get_existing_indices() + [-1]) + 1
        self.logfile = self.log_path/f'log{index}.log'

    def _get_existing_info(self):
        files = list(self.log_path.glob(r'log*.log'))
        match = [(x, self.template.match(x.name)) for x in files]
        return [x for x in match if not x is None]

    def get_existing_files(self):
        return [x[0] for x in self._get_existing_info()]

    def get_existing_indices(self):
        return [int(x[1].groups()[0][0]) for x in self._get_existing_info()]

def print_help(bot, message):
    bot.send_message(message.from_user.id, '/start to get data')

def process(bot, message):
    cam = cv2.VideoCapture(config['camera_id'])
    s, img = cam.read()
    if s:
        buf = io.BytesIO()
        buf.write(bytes(cv2.imencode('.jpg', img)[1]))
        buf.seek(0)
        bot.send_photo(message.from_user.id, buf)
        del buf
    else:
        bot.send_message(message.from_user.id, 'Cannot read data from cam')
    cam.release()

def get_stat(bot, message):
    if message.chat.username != 'eshalnov':
        process_unknown(bot, message)
    stat = '\n'.join([f.read_text() for f in args.log_rotator.get_existing_files()])
    bot.send_message(message.from_user.id, stat)

def process_unknown(bot, message):
    bot.send_message(message.from_user.id, 'Unknow command.\n/help to get availabe commands')

CMD = {'/start': process,
       '/stat': get_stat,
       '/help': print_help}

args = parse_args()
args.log_rotator = LogRotator(args)
print(args.log_rotator.logfile)
logging.basicConfig(format='%(asctime)-15s %(message)s', filename=str(args.log_rotator.logfile), level=logging.INFO)
config = json.loads(args.config.read_text())

bot = telebot.TeleBot(config['token'])

@bot.message_handler(content_types=['text'])
def get_text_message(message):
    logging.info(f'message {message.text} from {message.chat.username}')
    cmd = CMD.get(message.text, process_unknown)
    try:
        cmd(bot, message)
    except Exception as err:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)

bot.polling(none_stop=True, interval=0)
