import json
import time

from bs4 import BeautifulSoup

from common import util
from common.logger import log
from common.proxy import my_proxy
from query_task import QueryTask


class QueryHuya(QueryTask):
    def __init__(self, config):
        super().__init__(config)
        self.room_id_list = config.get("room_id_list", [])

    def query(self):
        if not self.enable:
            return
        try:
            current_time = time.strftime("%H:%M", time.localtime(time.time()))
            if self.begin_time <= current_time <= self.end_time:
                my_proxy.current_proxy_ip = my_proxy.get_proxy(proxy_check_url="https://www.huya.com")
                if self.enable_living_check:
                    for room_id in self.room_id_list:
                        self.query_live_status(room_id)
        except Exception as e:
            log.error(f"【虎牙-查询任务-{self.name}】出错：{e}", exc_info=True)

    def query_live_status(self, room_id=None):
        if room_id is None:
            return
        query_url = f'https://www.huya.com/{room_id}'
        response = util.requests_get(query_url, f"虎牙-查询直播状态-{self.name}", use_proxy=True)
        if util.check_response_is_ok(response):
            if len(response.text) == 0:
                log.error(f"【虎牙-查询直播状态-{self.name}】请求返回数据为空，room_id：{room_id}")
                return
            html_text = response.text
            soup = BeautifulSoup(html_text, "html.parser")
            scripts = soup.findAll("script")
            result = None
            for script in scripts:
                if script.string is not None and "stream: " in script.string:
                    try:
                        result = json.loads(script.string.split('stream: ')[1].split('};')[0].replace("undefined", "null"))
                    except TypeError:
                        log.error(f"【虎牙-查询直播状态-{self.name}】json解析错误，room_id：{room_id}")
                        return None
                    break

            if result is None:
                log.error(f"【虎牙-查询直播状态-{self.name}】请求返回数据为空，room_id：{room_id}")
                return

            try:
                game_stream_info_list = result.get('data')[0].get('gameStreamInfoList')
                game_live_info = result.get('data')[0].get('gameLiveInfo')
                username = game_live_info.get('nick')
            except AttributeError:
                log.error(f"【虎牙-查询直播状态-{self.name}】dict取值错误，room_id：{room_id}")
                return

            live_status = len(game_stream_info_list) > 0

            if self.living_status_dict.get(room_id, None) is None:
                self.living_status_dict[room_id] = live_status
                log.info(f"【虎牙-查询直播状态-{self.name}】【{username}】初始化")
                return

            if self.living_status_dict.get(room_id, None) != live_status:
                self.living_status_dict[room_id] = live_status

                if live_status is True:
                    room_name = game_live_info.get('roomName', '')
                    screenshot = game_live_info.get('screenshot', '').split('?')[0]
                    log.info(f"【虎牙-查询直播状态-{self.name}】【{username}】开播了，准备推送：{room_name}")
                    self.push_for_huya_live(username=username, room_title=room_name, jump_url=query_url, room_cover_url=screenshot)

    def push_for_huya_live(self, username=None, room_title=None, jump_url=None, room_cover_url=None):
        """
        虎牙直播提醒推送
        :param username: 主播名称
        :param room_title: 直播间标题
        :param jump_url: 跳转地址
        :param room_cover_url: 直播间封面
        """
        title = f"【虎牙】【{username}】开播了"
        super().push(title, room_title, jump_url, room_cover_url)
