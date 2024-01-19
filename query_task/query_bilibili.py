import json
import time
from collections import deque

from common import util
from common.logger import log
from common.proxy import my_proxy
from query_task import QueryTask


class QueryBilibili(QueryTask):
    def __init__(self, config):
        super().__init__(config)
        self.uid_list = config.get("uid_list", [])

    def query(self):
        if not self.enable:
            return
        try:
            current_time = time.strftime("%H:%M", time.localtime(time.time()))
            if self.begin_time <= current_time <= self.end_time:
                my_proxy.current_proxy_ip = my_proxy.get_proxy(proxy_check_url="http://api.bilibili.com/x/space/acc/info")
                if self.enable_dynamic_check:
                    for uid in self.uid_list:
                        self.query_dynamic(uid)
                if self.enable_living_check:
                    self.query_live_status_batch(self.uid_list)
        except Exception as e:
            log.error(f"【B站-查询任务-{self.name}】出错：{e}", exc_info=True)

    def query_dynamic(self, uid=None):
        if uid is None:
            return
        uid = str(uid)
        query_url = (f"http://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history"
                     f"?host_uid={uid}&offset_dynamic_id=0&need_top=0&platform=web&my_ts={int(time.time())}")
        headers = self.get_headers(uid)
        response = util.requests_get(query_url, f"B站-查询动态状态-{self.name}", headers=headers, use_proxy=True)
        if util.check_response_is_ok(response):
            try:
                result = json.loads(str(response.content, "utf-8"))
            except UnicodeDecodeError:
                log.error(f"【B站-查询动态状态-{self.name}】【{uid}】解析content出错")
                return
            if result["code"] != 0:
                log.error(f"【B站-查询动态状态-{self.name}】请求返回数据code错误：{result['code']}")
            else:
                data = result["data"]
                if len(data["cards"]) == 0:
                    log.debug(f"【B站-查询动态状态-{self.name}】【{uid}】动态列表为空")
                    return

                item = data["cards"][0]
                dynamic_id = item["desc"]["dynamic_id"]
                try:
                    uname = item["desc"]["user_profile"]["info"]["uname"]
                except KeyError:
                    log.error(f"【B站-查询动态状态-{self.name}】【{uid}】获取不到uname")
                    return

                if self.dynamic_dict.get(uid, None) is None:
                    self.dynamic_dict[uid] = deque(maxlen=self.len_of_deque)
                    cards = data["cards"]
                    for index in range(self.len_of_deque):
                        if index < len(cards):
                            self.dynamic_dict[uid].appendleft(cards[index]["desc"]["dynamic_id"])
                    log.info(f"【B站-查询动态状态-{self.name}】【{uname}】动态初始化：{self.dynamic_dict[uid]}")
                    return

                if dynamic_id not in self.dynamic_dict[uid]:
                    previous_dynamic_id = self.dynamic_dict[uid].pop()
                    self.dynamic_dict[uid].append(previous_dynamic_id)
                    log.info(f"【B站-查询动态状态-{self.name}】【{uname}】上一条动态id[{previous_dynamic_id}]，本条动态id[{dynamic_id}]")
                    self.dynamic_dict[uid].append(dynamic_id)
                    log.debug(self.dynamic_dict[uid])

                    dynamic_type = item["desc"]["type"]
                    if dynamic_type not in [2, 4, 8, 64]:
                        log.info(f"【B站-查询动态状态-{self.name}】【{uname}】动态有更新，但不在需要推送的动态类型列表中")
                        return

                    timestamp = item["desc"]["timestamp"]
                    dynamic_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
                    card_str = item["card"]
                    card = json.loads(card_str)

                    content = None
                    pic_url = None
                    if dynamic_type == 1:
                        # 转发动态
                        content = card["item"]["content"]
                    elif dynamic_type == 2:
                        # 图文动态
                        content = card["item"]["description"]
                        pic_url = card["item"]["pictures"][0]["img_src"]
                    elif dynamic_type == 4:
                        # 文字动态
                        content = card["item"]["content"]
                    elif dynamic_type == 8:
                        # 投稿动态
                        content = card["title"]
                        pic_url = card["pic"]
                    elif dynamic_type == 64:
                        # 专栏动态
                        content = card["title"]
                        pic_url = card["image_urls"][0]
                    log.info(f"【B站-查询动态状态-{self.name}】【{uname}】动态有更新，准备推送：{content[:30]}")
                    self.push_for_bili_dynamic(uname, dynamic_id, content, pic_url, dynamic_type, dynamic_time)

    def query_live_status_batch(self, uid_list=None):
        if uid_list is None:
            uid_list = []
        if len(uid_list) == 0:
            return
        query_url = "https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids"
        headers = self.get_headers(uid_list[0])
        data = json.dumps({
            "uids": list(map(int, uid_list))
        })
        response = util.requests_post(query_url, "B站-查询直播状态", headers=headers, data=data, use_proxy=True)
        if util.check_response_is_ok(response):
            result = json.loads(str(response.content, "utf-8"))
            if result["code"] != 0:
                log.error(f"【B站-查询直播状态-{self.name}】请求返回数据code错误：{result['code']}")
            else:
                live_status_list = result["data"]
                for uid, item_info in live_status_list.items():
                    try:
                        uname = item_info["uname"]
                        live_status = item_info["live_status"]
                    except (KeyError, TypeError):
                        log.error(f"【B站-查询直播状态-{self.name}】【{uid}】获取不到live_status")
                        continue

                    if self.living_status_dict.get(uid, None) is None:
                        self.living_status_dict[uid] = live_status
                        log.info(f"【B站-查询直播状态-{self.name}】【{uname}】初始化")
                        continue

                    if self.living_status_dict.get(uid, None) != live_status:
                        self.living_status_dict[uid] = live_status

                        room_id = item_info["room_id"]
                        room_title = item_info["title"]
                        room_cover_url = item_info["cover_from_user"]

                        if live_status == 1:
                            log.info(f"【B站-查询直播状态-{self.name}】【{uname}】开播了，准备推送：{room_title}")
                            self.push_for_bili_live(uname, room_id, room_title, room_cover_url)

    @staticmethod
    def get_headers(uid):
        return {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "cookie": "l=v;",
            "origin": "https://space.bilibili.com",
            "pragma": "no-cache",
            "referer": f"https://space.bilibili.com/{uid}/dynamic",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
        }

    def push_for_bili_dynamic(self, uname=None, dynamic_id=None, content=None, pic_url=None, dynamic_type=None, dynamic_time=None):
        """
        B站动态提醒推送
        :param uname: up主名字
        :param dynamic_id: 动态id
        :param content: 动态内容
        :param pic_url: 动态图片
        :param dynamic_type: 动态类型
        :param dynamic_time: 动态发送时间
        """
        if uname is None or dynamic_id is None or content is None:
            log.error(f"【B站-动态提醒推送-{self.name}】缺少参数，uname:[{uname}]，dynamic_id:[{dynamic_id}]，content:[{content[:30]}]")
            return

        title_msg = "发动态了"
        if dynamic_type == 1:
            title_msg = "转发了动态"
        elif dynamic_type == 8:
            title_msg = "投稿了"
        title = f"【B站】【{uname}】{title_msg}"
        content = f"{content[:100] + (content[100:] and '...')}[{dynamic_time}]"
        dynamic_url = f"https://www.bilibili.com/opus/{dynamic_id}"
        super().push(title, content, dynamic_url, pic_url)

    def push_for_bili_live(self, uname=None, room_id=None, room_title=None, room_cover_url=None):
        """
        B站直播提醒推送
        :param uname: up主名字
        :param room_id: 直播间id
        :param room_title: 直播间标题
        :param room_cover_url: 直播间封面
        """
        title = f"【B站】【{uname}】开播了"
        live_url = f"https://live.bilibili.com/{room_id}"
        super().push(title, room_title, live_url, room_cover_url)
