# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json
import os.path

# useful for handling different item types with a single interface
from youtube.items import YoutubeItem
from youtube.spiders.youtube import Youtuber


class YoutubePipeline:
    def __init__(self):
        self._file_count = 0
        self._file_info_list = {}
        self._command_list = {}

    def close_spider(self, spider: Youtuber):
        for name in self._file_info_list.keys():
            final_path = os.path.join(spider.settings.get('DOWNLOAD_PATH'), name)
            command_file = os.path.join(spider.settings.get('DOWNLOAD_PATH'), name, 'command.txt')
            info_file = os.path.join(spider.settings.get('DOWNLOAD_PATH'), name, 'file_info.json')
            if not os.path.exists(final_path):
                os.makedirs(final_path)

            with open(command_file, 'w') as f:
                f.writelines(self._command_list.get(name))

            with open(info_file, 'w') as f:
                json.dump(self._file_info_list.get(name), f, ensure_ascii=False, indent=4)

    def process_item(self, item: YoutubeItem, spider: Youtuber):
        if not isinstance(item, YoutubeItem):
            return item
        video_id = item.get('video_id')
        video_title = item.get('video_title')
        name = item.get('youtuber')
        info_list = self._file_info_list.get(name, {})
        info_list.update({self._file_count: video_title})
        self._file_info_list.update({name: info_list})
        final_path = os.path.join(spider.settings.get('DOWNLOAD_PATH'), name)
        prepare_command = (
            f'yt-dlp --embed-subs --sub-langs "zh,en" -S "quality,ext" --extractor-args '
            f'"youtube:lang=zh-CN" -P "{final_path}" -o "{self._file_count}.%(ext)s"'
            f' https://www.youtube.com/watch?v={video_id}'
        )
        self._file_count += 1

        command_list = self._command_list.get(name, [])
        command_list += (f'{prepare_command}\n',)
        self._command_list.update({name: command_list})
