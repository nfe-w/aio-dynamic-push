import datetime
import json
import re
import time
from collections import deque

from common import util
from common.logger import log
from common.proxy import my_proxy
from query_task import QueryTask


class QueryWeibo(QueryTask):
    def __init__(self, config):
        super().__init__(config)
        self.uid_list = config.get("uid_list", [])

    def query(self):
        if not self.enable:
            return
        try:
            current_time = time.strftime("%H:%M", time.localtime(time.time()))
            if self.begin_time <= current_time <= self.end_time:
                my_proxy.current_proxy_ip = my_proxy.get_proxy(proxy_check_url="https://m.weibo.com")
                if self.enable_dynamic_check:
                    for uid in self.uid_list:
                        self.query_dynamic(uid)
        except Exception as e:
            log.error(f"【微博-查询任务-{self.name}】出错：{e}", exc_info=True)

    def query_dynamic(self, uid=None):
        if uid is None:
            return
        uid = str(uid)
        query_url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid=107603{uid}&count=25"
        headers = self.get_headers(uid)
        response = util.requests_get(query_url, f"微博-查询动态状态-{self.name}", headers=headers, use_proxy=True)
        if util.check_response_is_ok(response):
            result = json.loads(str(response.content, "utf-8"))
            cards = result["data"]["cards"]
            if len(cards) == 0:
                super().handle_for_result_null("-1", uid, "微博", uid)
                return

            # 循环遍历 cards ，剔除不满足要求的数据
            cards = [card for card in cards if
                     card.get("mblog") is not None  # 跳过不包含 mblog 的数据
                     and card["mblog"].get("isTop", None) != 1  # 跳过置顶
                     and card["mblog"].get("mblogtype", None) != 2  # 跳过置顶
                     ]

            # 跳过置顶后再判断一下，防止越界
            if len(cards) == 0:
                super().handle_for_result_null("-1", uid, "微博", uid)
                return

            card = cards[0]
            mblog = card["mblog"]
            mblog_id = mblog["id"]
            user = mblog["user"]
            screen_name = user["screen_name"]

            if self.dynamic_dict.get(uid, None) is None:
                self.dynamic_dict[uid] = deque(maxlen=self.len_of_deque)
                for index in range(self.len_of_deque):
                    if index < len(cards):
                        self.dynamic_dict[uid].appendleft(cards[index]["mblog"]["id"])
                log.info(f"【微博-查询动态状态-{self.name}】【{screen_name}】动态初始化：{self.dynamic_dict[uid]}")
                return

            if mblog_id not in self.dynamic_dict[uid]:
                previous_mblog_id = self.dynamic_dict[uid].pop()
                self.dynamic_dict[uid].append(previous_mblog_id)
                log.info(f"【微博-查询动态状态-{self.name}】【{screen_name}】上一条动态id[{previous_mblog_id}]，本条动态id[{mblog_id}]")
                self.dynamic_dict[uid].append(mblog_id)
                log.debug(self.dynamic_dict[uid])

                card_type = card["card_type"]
                if card_type not in [9]:
                    log.info(f"【微博-查询动态状态-{self.name}】【{screen_name}】动态有更新，但不在需要推送的动态类型列表中")
                    return

                # 如果动态发送日期早于昨天，则跳过（既能避免因api返回历史内容导致的误推送，也可以兼顾到前一天停止检测后产生的动态）
                created_at = time.strptime(mblog["created_at"], "%a %b %d %H:%M:%S %z %Y")
                created_at_ts = time.mktime(created_at)
                yesterday = (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d")
                yesterday_ts = time.mktime(time.strptime(yesterday, "%Y-%m-%d"))
                if created_at_ts < yesterday_ts:
                    log.info(f"【微博-查询动态状态-{self.name}】【{screen_name}】动态有更新，但动态发送时间早于今天，可能是历史动态，不予推送")
                    return
                dynamic_time = time.strftime("%Y-%m-%d %H:%M:%S", created_at)

                content = None
                pic_url = None
                jump_url = None
                if card_type == 9:
                    text = mblog["text"]
                    text = re.sub(r"<[^>]+>", "", text)
                    content = mblog["raw_text"] if mblog.get("raw_text", None) is not None else text
                    pic_url = mblog.get("original_pic", None)
                    jump_url = card["scheme"]
                log.info(f"【微博-查询动态状态-{self.name}】【{screen_name}】动态有更新，准备推送：{content[:30]}")
                self.push_for_weibo_dynamic(screen_name, mblog_id, content, pic_url, jump_url, dynamic_time, dynamic_raw_data=card)

    @staticmethod
    def get_headers(uid):
        return {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "mweibo-pwa": "1",
            "referer": f"https://m.weibo.cn/u/{uid}",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "x-requested-with": "XMLHttpRequest",
        }

    def push_for_weibo_dynamic(self, username=None, mblog_id=None, content=None, pic_url=None, jump_url=None, dynamic_time=None, dynamic_raw_data=None):
        """
        微博动态提醒推送
        :param username: 博主名
        :param mblog_id: 动态id
        :param content: 动态内容
        :param pic_url: 图片地址
        :param jump_url: 跳转地址
        :param dynamic_time: 动态发送时间
        :param dynamic_raw_data: 动态原始数据
        """
        if username is None or mblog_id is None or content is None:
            log.error(f"【微博-动态提醒推送-{self.name}】缺少参数，username:[{username}]，mblog_id:[{mblog_id}]，content:[{content[:30]}]")
            return
        title = f"【微博】【{username}】发微博了"
        content = f"{content[:100] + (content[100:] and '...')}[{dynamic_time}]"
        super().push(title, content, jump_url, pic_url, extend_data={'dynamic_raw_data': dynamic_raw_data})
