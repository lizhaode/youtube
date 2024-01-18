# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import shlex
import subprocess
import urllib.parse

# useful for handling different item types with a single interface
from youtube.items import YoutubeItem
from youtube.spiders.youtube import Youtuber


class YoutubePipeline:
    def process_item(self, item: YoutubeItem, spider: Youtuber):
        if not isinstance(item, YoutubeItem):
            return item
        video_id = item.get('video_id')
        if spider.settings.getbool('FILE_NAME_BASE64'):
            video_title = urllib.parse.quote(item.get('video_title'))
        else:
            video_title = item.get('video_title')
        path = spider.settings.get('DOWNLOAD_PATH')
        prepare_command = f'yt-dlp --embed-subs --sub-langs "zh,en" -S "quality,ext" --extractor-args "youtube:lang=zh-CN" -P {path} -o "{video_title}.%(ext)s" https://www.youtube.com/watch?v={video_id}'
        spider.logger.error(f'execute: {prepare_command}')
        subprocess.run(
            shlex.split(prepare_command), check=True, capture_output=False
        )
