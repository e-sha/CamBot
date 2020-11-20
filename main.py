import telebot
import json
from pathlib import Path
import sys
import cv2
import traceback
import io
from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', help='path to a config file', type=Path)
    return parser.parse_args()

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

def process_unknown(bot, message):
    bot.send_message(message.from_user.id, 'Unknow command.\n/help to get availabe commands')

CMD = {'/start': process,
       '/help': print_help}

args = parse_args()
config = json.loads(args.config.read_text())

bot = telebot.TeleBot(config['token'])

@bot.message_handler(content_types=['text'])
def get_text_message(message):
    cmd = CMD.get(message.text, process_unknown)
    try:
        cmd(bot, message)
    except Exception as err:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)

bot.polling(none_stop=True, interval=0)
