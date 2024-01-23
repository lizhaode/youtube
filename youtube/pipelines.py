# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json
import os.path
import shlex
import subprocess

# useful for handling different item types with a single interface
from youtube.items import YoutubeItem
from youtube.spiders.youtube import Youtuber


class YoutubePipeline:
    def __init__(self):
        self._file_count = 0

    def open_spider(self, spider: Youtuber):
        if os.path.exists('file_info.json'):
            os.remove('file_info.json')

    def process_item(self, item: YoutubeItem, spider: Youtuber):
        if not isinstance(item, YoutubeItem):
            return item
        video_id = item.get('video_id')
        video_title = item.get('video_title')
        if os.path.exists('file_info.json'):
            with open('file_info.json') as f:
                base = json.load(f)
        else:
            base = []
        base += ({self._file_count: video_title},)
        with open('file_info.json', 'w') as f:
            json.dump(base, f, ensure_ascii=False, indent=2)

        path = spider.settings.get('DOWNLOAD_PATH')
        prepare_command = f'yt-dlp --embed-subs --sub-langs "zh,en" -S "quality,ext" --extractor-args "youtube:lang=zh-CN" -P {path} -o "{self._file_count}.%(ext)s" https://www.youtube.com/watch?v={video_id}'
        self._file_count += 1
        spider.logger.error(f'execute: {prepare_command}')
        with open('command.txt', 'a+') as f:
            f.write(prepare_command + '\n')
        # subprocess.run(
        #     shlex.split(prepare_command), check=True, capture_output=True
        # )
