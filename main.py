import json
import logging
import os
import random
import shlex
import subprocess
import sys
from concurrent.futures.thread import ThreadPoolExecutor

from youtube.settings import DOWNLOAD_PATH

log = logging.getLogger(__name__)
std_out = logging.StreamHandler(sys.stdout)
std_out.setFormatter(logging.Formatter(fmt='%(asctime)s-%(threadName)s:%(lineno)d:%(message)s'))
log.addHandler(std_out)

log.setLevel(logging.INFO)


def start_down(down_info: dict) -> None:
    file_number = down_info.get('command').split(' ')[-2].split('.')[0].strip('"')
    with open(os.path.join(DOWNLOAD_PATH, down_info.get('youtuber'), 'file_info.json')) as info:
        file_info = json.load(info)
    log.info('start to download: %s', file_info.get(file_number))
    try:
        subprocess.run(
            shlex.split(down_info.get('command')),
            capture_output=True,
            check=True,
        )
        log.info('success downloaded: %s', file_info.get(file_number))
    except subprocess.CalledProcessError:
        log.info('failed downloaded: %s', file_info.get(file_number))


def main():
    download_info = []
    for parent_path in os.listdir(DOWNLOAD_PATH):
        with open(os.path.join(DOWNLOAD_PATH, parent_path, 'command.txt')) as f:
            log.info('read youtuber: %s download info', parent_path)
            download_info += [{'command': i, 'youtuber': parent_path} for i in f]

    random.shuffle(download_info)

    with ThreadPoolExecutor(max_workers=5) as tpe:
        tpe.map(start_down, download_info)


if __name__ == '__main__':
    main()
