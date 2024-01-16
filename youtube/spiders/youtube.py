from typing import Any, Iterable

import js2py
import scrapy
from scrapy import Request
from scrapy.exceptions import CloseSpider
from scrapy.http import JsonRequest, Response

from youtube.items import YoutubeItem


class Youtuber(scrapy.Spider):
    name = 'youtuber'

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            f'https://www.youtube.com/{self.settings.get("YOUTUBER")}/videos'
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        head_script_gen = filter(
            lambda x: 'var ytcfg=' in x or 'window.ytplayer={}' in x,
            response.css('head').css('script').getall(),
        )
        head_script_js = next(head_script_gen).split('">')[1].strip('</script>')
        head_script_js = (
            head_script_js
            + next(head_script_gen)
            .split('ytplayer={};')[1]
            .split('window.ytcfg.obfuscatedData')[0]
            .strip('</script>')
            .strip()
        )
        ytcfg = js2py.eval_js(head_script_js + 'ytcfg').to_dict()
        url_api_key = ytcfg.get('data_').get('INNERTUBE_API_KEY')
        json_body_context = ytcfg.get('data_').get('INNERTUBE_CONTEXT')

        if (not url_api_key) or (not json_body_context):
            self.logger.error('next video page request can not create')
            raise CloseSpider('unexpected error')

        body_script_js = next(
            filter(
                lambda x: 'ytInitialData' in x,
                response.css('body').css('script').getall(),
            )
        )
        body_script_js = body_script_js.split('>')[1].strip('</script')
        video_contents = (
            js2py.eval_js(body_script_js)
            .to_dict()
            .get('contents')
            .get('twoColumnBrowseResultsRenderer')
            .get('tabs')[1]
            .get('tabRenderer')
            .get('content')
            .get('richGridRenderer')
            .get('contents')
        )
        item_list, req = self.parse_json_video_info(
            video_contents, url_api_key, json_body_context
        )
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
            response.cb_kwargs.get('api_key'),
            response.cb_kwargs.get('context'),
        )
        yield req
        for i in item_list:
            yield i

    def parse_json_video_info(
        self, video_contents: list[dict], api_key: str, context: str
    ) -> tuple:
        item_list = []
        request = None
        for info in video_contents:
            if 'richItemRenderer' in info:
                if (
                    len(
                        info.get('richItemRenderer')
                        .get('content')
                        .get('videoRenderer')
                        .get('title')
                        .get('runs')
                    )
                    != 1
                ):
                    self.logger.error(
                        f"video title unexpected: {info.get('richItemRenderer').get('content').get('videoRenderer').get('title').get('runs')}"
                    )
                item_list += (
                    YoutubeItem(
                        video_id=info.get('richItemRenderer')
                        .get('content')
                        .get('videoRenderer')
                        .get('videoId'),
                        video_title=
                            info.get('richItemRenderer')
                            .get('content')
                            .get('videoRenderer')
                            .get('title')
                            .get('runs')[0]
                            .get('text'),
                            'zh-cn',
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
                    cb_kwargs={'api_key': api_key, 'context': context},
                )
        self.logger.error(f'got {len(item_list)} videos')
        return item_list, request
