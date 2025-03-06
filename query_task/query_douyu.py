import json
import time

from common import util
from common.logger import log
from common.proxy import my_proxy
from query_task import QueryTask


class QueryDouyu(QueryTask):
    def __init__(self, config):
        super().__init__(config)
        self.room_id_list = config.get("room_id_list", [])

    def query(self):
        if not self.enable:
            return
        try:
            current_time = time.strftime("%H:%M", time.localtime(time.time()))
            if self.begin_time <= current_time <= self.end_time:
                my_proxy.current_proxy_ip = my_proxy.get_proxy(proxy_check_url="https://www.douyu.com")
                if self.enable_living_check:
                    for room_id in self.room_id_list:
                        self.query_live_status(room_id)
        except Exception as e:
            log.error(f"【斗鱼-查询任务-{self.name}】出错：{e}", exc_info=True)

    def query_live_status(self, room_id=None):
        if room_id is None:
            return
        query_url = f'https://www.douyu.com/betard/{room_id}'
        response = util.requests_get(query_url, f"斗鱼-查询直播状态-{self.name}", use_proxy=True)
        if util.check_response_is_ok(response):
            try:
                result = json.loads(str(response.content, "utf-8"))
            except UnicodeDecodeError:
                log.error(f"【斗鱼-查询直播状态-{self.name}】【{room_id}】解析content出错")
                return

            if result is None:
                log.error(f"【斗鱼-查询直播状态-{self.name}】【{room_id}】请求返回数据为空")
                return

            room_info = result.get('room')
            if room_info is None:
                log.error(f"【斗鱼-查询直播状态-{self.name}】【{room_id}】请求返回数据room为空")

            try:
                username = room_info.get('nickname')
            except AttributeError:
                log.error(f"【斗鱼-查询直播状态-{self.name}】dict取值错误，room_id：{room_id}")
                return

            avatar_url = None
            try:
                avatar_url = room_info.get('avatar').get('small')
            except Exception:
                log.error(f"【斗鱼-查询直播状态-{self.name}】头像获取发生错误，room_id：{room_id}")

            show_status = room_info['show_status']

            if self.living_status_dict.get(room_id, None) is None:
                self.living_status_dict[room_id] = show_status
                log.info(f"【斗鱼-查询直播状态-{self.name}】【{username}】初始化")
                return

            if self.living_status_dict.get(room_id, None) != show_status:
                self.living_status_dict[room_id] = show_status

                if show_status == 1:
                    room_name = room_info.get('room_name')
                    room_pic = room_info.get('room_pic')
                    log.info(f"【斗鱼-查询直播状态-{self.name}】【{username}】开播了，准备推送：{room_name}")
                    self.push_for_douyu_live(username=username, room_title=room_name, jump_url=f'https://www.douyu.com/{room_id}', room_cover_url=room_pic, avatar_url=avatar_url)

    def push_for_douyu_live(self, username=None, room_title=None, jump_url=None, room_cover_url=None, avatar_url=None):
        """
        斗鱼直播提醒推送
        :param username: 主播名称
        :param room_title: 直播间标题
        :param jump_url: 跳转地址
        :param room_cover_url: 直播间封面
        :param avatar_url: 头像url
        """
        title = f"【斗鱼】【{username}】开播了"
        extend_data = {
            'avatar_url': avatar_url,
        }
        super().push(title, room_title, jump_url, room_cover_url, extend_data=extend_data)
