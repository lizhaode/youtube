import json
import os
import shlex
import subprocess
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime

from youtube.settings import DOWNLOAD_PATH


def start_down(command: str) -> None:
    file_number = command.split(' ')[-2].split('.')[0].strip('"')
    with open(os.path.join(DOWNLOAD_PATH, parent_path, 'file_info.json')) as info:
        file_info = json.load(info)
    print(f'[{datetime.today().strftime("%Y-%m-%d %H:%M:%S")}] start to download: {file_info.get(file_number)}')
    subprocess.run(shlex.split(command), capture_output=True, check=True)
    print(f'[{datetime.today().strftime("%Y-%m-%d %H:%M:%S")}] success downloaded: {file_info.get(file_number)}')


if __name__ == '__main__':
    for parent_path in os.listdir(DOWNLOAD_PATH):
        with open(os.path.join(DOWNLOAD_PATH, parent_path, 'command.txt')) as f:
            with ThreadPoolExecutor(max_workers=5) as tpe:
                tpe.map(start_down, f)
