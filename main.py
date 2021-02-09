from argparse import ArgumentParser
import json
from pathlib import Path

from cvbot import Bot


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-c',
                        '--config',
                        help='path to a config file',
                        type=Path)
    parser.add_argument('-l',
                        '--logpath',
                        help='path to a directory with log files',
                        type=Path)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    config = json.loads(args.config.read_text())
    args.config.unlink()
    args.__dict__.pop('config')
    processor = Processor(config['camera_id'])
    Bot(config.pop('token', None), processor, args.logpath)
