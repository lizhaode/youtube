from typing import Any, Iterable

import scrapy
import yaml
from scrapy import Request
from scrapy.exceptions import CloseSpider
from scrapy.http import JsonRequest, Response
from zhconv import convert

from youtube.items import YoutubeItem


class Youtuber(scrapy.Spider):
    name = 'youtuber'

    def start_requests(self) -> Iterable[Request]:
        for youtuber in self.settings.getlist("YOUTUBER_LIST"):
            yield Request(f'https://www.youtube.com/{youtuber}/videos')

    def parse(self, response: Response, **kwargs: Any) -> Any:
        youtuber_name = response.css('title::text').get().split('-')[0].strip()

        head_script = yaml.safe_load(
            [head_js for head_js in response.css('head').css('script').getall() if 'window.ytplayer={}' in head_js][0]
            .split('ytcfg.set(')[1]
            .split(');')[0]
        )
        url_api_key = head_script.get('INNERTUBE_API_KEY')
        json_body_context = head_script.get('INNERTUBE_CONTEXT')

        if (not url_api_key) or (not json_body_context):
            self.logger.error('next video page request can not create')
            raise CloseSpider('unexpected error')

        body_script = (
            [body_js for body_js in response.css('body').css('script::text').getall() if 'ytInitialData' in body_js][0]
            .replace('var ytInitialData =', '')
            .strip(';')
        )
        video_contents = (
            yaml.safe_load(body_script)
            .get('contents')
            .get('twoColumnBrowseResultsRenderer')
            .get('tabs')[1]
            .get('tabRenderer')
            .get('content')
            .get('richGridRenderer')
            .get('contents')
        )
        item_list, req = self.parse_json_video_info(video_contents, youtuber_name, url_api_key, json_body_context)
        yield req
        for i in item_list:
            yield i

    def next_page(self, response: Response, **kwargs: Any) -> Any:
        video_contents = (
            response.json()
            .get('onResponseReceivedActions')[0]
            .get('appendContinuationItemsAction')
            .get('continuationItems')
        )
        item_list, req = self.parse_json_video_info(
            video_contents,
            response.cb_kwargs.get('youtuber_name'),
            response.cb_kwargs.get('api_key'),
            response.cb_kwargs.get('context'),
        )
        yield req
        for i in item_list:
            yield i

    def parse_json_video_info(
        self, video_contents: list[dict], youtuber_name: str, api_key: str, context: str
    ) -> tuple:
        item_list = []
        request = None
        for info in video_contents:
            if 'richItemRenderer' in info:
                if len(info.get('richItemRenderer').get('content').get('videoRenderer').get('title').get('runs')) != 1:
                    self.logger.error(
                        f"video title unexpected: {info.get('richItemRenderer').get('content').get('videoRenderer').get('title').get('runs')}"
                    )
                item_list += (
                    YoutubeItem(
                        video_id=info.get('richItemRenderer').get('content').get('videoRenderer').get('videoId'),
                        video_title=convert(
                            info.get('richItemRenderer')
                            .get('content')
                            .get('videoRenderer')
                            .get('title')
                            .get('runs')[0]
                            .get('text'),
                            'zh-cn',
                        ),
                        youtuber=youtuber_name,
                    ),
                )

            elif 'continuationItemRenderer' in info:
                request = JsonRequest(
                    url=f'https://www.youtube.com/youtubei/v1/browse?key={api_key}&prettyPrint=false',
                    data={
                        'context': context,
                        'continuation': info.get('continuationItemRenderer')
                        .get('continuationEndpoint')
                        .get('continuationCommand')
                        .get('token'),
                    },
                    callback=self.next_page,
                    cb_kwargs={'api_key': api_key, 'context': context, 'youtuber_name': youtuber_name},
                )
        self.logger.warning(f'from {youtuber_name} got {len(item_list)} videos')
        return item_list, request
