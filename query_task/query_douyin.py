import json
import time
from collections import deque
from urllib import parse

import requests
from bs4 import BeautifulSoup
from requests.utils import dict_from_cookiejar

from common import util
from common.cache import set_cached_value, get_cached_value
from common.logger import log
from common.proxy import my_proxy
from query_task import QueryTask

class QueryDouyin(QueryTask):
    def __init__(self, config):
        super().__init__(config)
        self.signature_server_url = config.get("signature_server_url", "")
        self.username_list = config.get("username_list", [])
        self.sec_uid_list = config.get("sec_uid_list", [])
        self.douyin_id_list = config.get("douyin_id_list", [])
        self.ttwid = None

    def query(self):
        if not self.enable:
            return
        try:
            self.init_ttwid()
            current_time = time.strftime("%H:%M", time.localtime(time.time()))
            if self.begin_time <= current_time <= self.end_time:
                my_proxy.current_proxy_ip = my_proxy.get_proxy(proxy_check_url="https://www.iesdouyin.com/web/api/v2/aweme/post")
                if self.enable_dynamic_check:
                    for i in range(len(self.username_list)):
                        self.query_dynamic(self.username_list[i], self.sec_uid_list[i])
                if self.enable_living_check:
                    for douyin_id in self.douyin_id_list:
                        self.query_live_status_v3(douyin_id)
        except Exception as e:
            log.error(f"【抖音-查询任务-{self.name}】出错：{e}", exc_info=True)

    def get_signature(self):
        # noinspection PyBroadException
        try:
            return requests.get(self.signature_server_url).text
        except Exception:
            log.error("【抖音-获取签名】连接失败")
            return ""

    def init_ttwid(self, get_from_cache=True):
        ttwid = None
        if get_from_cache:
            ttwid = get_cached_value("ttwid")
        if ttwid is None:
            ttwid = self.generate_ttwid()
            set_cached_value("ttwid", ttwid)
        self.ttwid = ttwid

    def generate_ttwid(self):
        url = "https://ttwid.bytedance.com/ttwid/union/register/"
        headers = self.get_headers()
        # 固定的内容
        body_data = {
            "region": "cn",
            "aid": 1768,
            "needFid": False,
            "service": "www.ixigua.com",
            "migrate_info": {
                "ticket": "",
                "source": "node"
            },
            "cbUrlProtocol": "https",
            "union": True
        }
        response = util.requests_post(url, f"抖音-生成ttwid-{self.name}", headers=headers, json=body_data)
        if util.check_response_is_ok(response):
            cookie_dict = dict_from_cookiejar(response.cookies)
            ttwid = cookie_dict.get('ttwid')
            log.info(f"【抖音-生成ttwid-{self.name}】成功：{ttwid}")
            return ttwid
        else:
            log.error(f"【抖音-生成ttwid-{self.name}】请求返回数据code错误：{response.status_code}")
            return None

    def query_dynamic(self, nickname=None, sec_uid=None):
        if nickname is None or sec_uid is None:
            return
        query_url = f"http://www.iesdouyin.com/web/api/v2/aweme/post?sec_uid={sec_uid}&count=21&max_cursor=0&aid=1128&_signature={self.get_signature()}"
        headers = self.get_headers()
        response = util.requests_get(query_url, f"抖音-查询动态状态-{self.name}", headers=headers, use_proxy=True)
        if util.check_response_is_ok(response):
            result = json.loads(str(response.content, "utf-8"))
            if result["status_code"] != 0:
                log.error(f"【抖音-查询动态状态-{self.name}】请求返回数据code错误：{result['status_code']}")
            else:
                aweme_list = result["aweme_list"]
                if len(aweme_list) == 0:
                    super().handle_for_result_null("-1", sec_uid, "抖音", nickname)
                    return

                aweme = aweme_list[0]
                aweme_id = aweme["aweme_id"]

                if self.dynamic_dict.get(sec_uid, None) is None:
                    self.dynamic_dict[sec_uid] = deque(maxlen=self.len_of_deque)
                    for index in range(self.len_of_deque):
                        if index < len(aweme_list):
                            self.dynamic_dict[sec_uid].appendleft(aweme_list[index]["aweme_id"])
                    log.info(f"【抖音-查询动态状态-{self.name}】【{nickname}】动态初始化：{self.dynamic_dict[sec_uid]}")
                    return

                if aweme_id not in self.dynamic_dict[sec_uid]:
                    previous_aweme_id = self.dynamic_dict[sec_uid].pop()
                    self.dynamic_dict[sec_uid].append(previous_aweme_id)
                    log.info(f"【抖音-查询动态状态-{self.name}】【{nickname}】上一条动态id[{previous_aweme_id}]，本条动态id[{aweme_id}]")
                    self.dynamic_dict[sec_uid].append(aweme_id)
                    log.debug(self.dynamic_dict[sec_uid])

                    try:
                        content = aweme["desc"]
                        pic_url = aweme["video"]["cover"]["url_list"][0]
                        video_url = f"https://www.douyin.com/video/{aweme_id}"
                        log.info(f"【抖音-查询动态状态-{self.name}】【{nickname}】动态有更新，准备推送：{content[:30]}")
                        self.push_for_douyin_dynamic(nickname, aweme_id, content, pic_url, video_url, dynamic_raw_data=aweme)
                    except AttributeError:
                        log.error(f"【抖音-查询动态状态-{self.name}】dict取值错误，nickname：{nickname}")
                        return

    @DeprecationWarning
    def query_live_status_v2(self, user_account=None):
        if user_account is None:
            return
        query_url = f"https://live.douyin.com/{user_account}?my_ts={int(time.time())}"
        headers = self.get_headers_for_live()
        response = util.requests_get(query_url, f"抖音-查询直播状态-{self.name}", headers=headers, use_proxy=True)
        if util.check_response_is_ok(response):
            html_text = response.text
            soup = BeautifulSoup(html_text, "html.parser")
            scripts = soup.findAll("script")
            result = None
            for script in scripts:
                if "nickname" in script.text:
                    script_string = script.string
                    unquote_string = parse.unquote(script_string)
                    # 截取最外层{}内的内容
                    json_string_with_escape = unquote_string[unquote_string.find("{"):unquote_string.rfind("}") + 1]
                    # 多层转义的去转义
                    json_string = json_string_with_escape.replace("\\\\", "\\").replace("\\\"", '"')
                    try:
                        result = json.loads(json_string)
                    except TypeError:
                        log.error(f"【抖音-查询直播状态-{self.name}】json解析错误，user_account：{user_account}")
                        return None
                    break

            if result is None:
                log.error(f"【抖音-查询直播状态-{self.name}】请求返回数据为空，user_account：{user_account}")
            else:
                try:
                    room_info = result["state"]["roomStore"]["roomInfo"]
                    room = room_info.get("room")
                    anchor = room_info.get("anchor")
                    nickname = anchor["nickname"]
                except AttributeError:
                    log.error(f"【抖音-查询直播状态-{self.name}】dict取值错误，user_account：{user_account}")
                    return

                if room is None:
                    if self.living_status_dict.get(user_account, None) is None:
                        self.living_status_dict[user_account] = "init"
                        log.info(f"【抖音-查询直播状态-{self.name}】【{nickname}】初始化")
                    return

                if room is not None:
                    live_status = room.get("status")
                    if self.living_status_dict.get(user_account, None) is None:
                        self.living_status_dict[user_account] = live_status
                        log.info(f"【抖音-查询直播状态-{self.name}】【{nickname}】初始化")
                        return

                    if self.living_status_dict.get(user_account, None) != live_status:
                        self.living_status_dict[user_account] = live_status

                        if live_status == 2:
                            name = nickname
                            room_title = room["title"]
                            room_cover_url = room["cover"]["url_list"][0]

                            log.info(f"【抖音-查询直播状态-{self.name}】【{nickname}】开播了，准备推送：{room_title}")
                            self.push_for_douyin_live(name, query_url, room_title, room_cover_url)

    def query_live_status_v3(self, user_account=None, is_retry_by_ttwid=False):
        if user_account is None:
            return
        query_url = "https://live.douyin.com/webcast/room/web/enter/"
        headers = self.get_headers_for_live()
        if self.ttwid is not None:
            headers['cookie'] = f"ttwid={self.ttwid}"
        params = {
            "aid": "6383",
            "device_platform": "web",
            "enter_from": "web_live",
            "cookie_enabled": "true",
            "browser_language": "zh-CN",
            "browser_platform": "Win32",
            "browser_name": "Chrome",
            "browser_version": "109.0.0.0",
            "web_rid": f"{user_account}",
            "a_bogus": "",
        }
        response = util.requests_get(query_url, f"抖音-查询直播状态-{self.name}", headers=headers, params=params, use_proxy=True)
        if util.check_response_is_ok(response):

            if len(response.content) == 0:
                log.error(f"【抖音-查询直播状态-{self.name}】请求返回数据为空，user_account：{user_account}")
                if is_retry_by_ttwid is True:
                    log.error(f"【抖音-查询直播状态-{self.name}】已经重试获取了ttwid【{user_account}】，但依然失败")
                    return
                self.init_ttwid(get_from_cache=False)
                log.info(f"【抖音-查询直播状态-{self.name}】重新获取到了ttwid：{self.ttwid}")
                log.info(f"【抖音-查询直播状态-{self.name}】重试获取【{user_account}】的动态")
                self.query_live_status_v3(user_account, is_retry_by_ttwid=True)
                return

            result = json.loads(str(response.content, "utf-8"))
            if result["status_code"] != 0:
                log.error(f"【抖音-查询直播状态-{self.name}】请求返回数据code错误：{result['status_code']}，user_account：{user_account}")
            else:
                data = result["data"]
                if data is None:
                    log.error(f"【抖音-查询直播状态-{self.name}】请求返回数据为空，user_account：{user_account}")
                    return
                room_datas = data.get('data')
                if room_datas is None or len(room_datas) == 0:
                    log.error(f"【抖音-查询直播状态-{self.name}】【{user_account}】疑似未开通直播间，跳过本次检测")
                    return
                try:
                    room_data = room_datas[0]
                    room_status = data.get('room_status')
                    nickname = data.get('user').get('nickname')
                except AttributeError:
                    log.error(f"【抖音-查询直播状态-{self.name}】dict取值错误，user_account：{user_account}")
                    return

                avatar_url = None
                try:
                    avatar_url = data.get('user').get('avatar_thumb').get('url_list')[0]
                except Exception:
                    log.error(f"【抖音-查询直播状态-{self.name}】头像获取发生错误，user_account：{user_account}")

                if self.living_status_dict.get(user_account, None) is None:
                    self.living_status_dict[user_account] = room_status
                    log.info(f"【抖音-查询直播状态-{self.name}】【{nickname}】初始化")
                    return

                if self.living_status_dict.get(user_account, None) != room_status:
                    self.living_status_dict[user_account] = room_status

                    if room_status == 0:
                        room_title = room_data["title"]
                        room_cover_url = room_data["cover"]["url_list"][0]
                        jump_url = f'https://live.douyin.com/{user_account}'

                        log.info(f"【抖音-查询直播状态-{self.name}】【{nickname}】开播了，准备推送：{room_title}")
                        self.push_for_douyin_live(nickname, jump_url, room_title, room_cover_url, avatar_url=avatar_url)

    @staticmethod
    def get_headers():
        return {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": "https://www.iesdouyin.com/",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "x-requested-with": "XMLHttpRequest",
        }

    @staticmethod
    def get_headers_for_live():
        return {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-site",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        }

    def push_for_douyin_dynamic(self, nickname=None, aweme_id=None, content=None, pic_url=None, video_url=None, dynamic_raw_data=None):
        """
        抖音动态提醒推送
        :param nickname: 作者名
        :param aweme_id: 动态id
        :param content: 动态内容
        :param pic_url: 封面图片
        :param video_url: 视频地址
        :param dynamic_raw_data: 动态原始数据
        """
        if nickname is None or aweme_id is None or content is None:
            log.error(f"【抖音-动态提醒推送-{self.name}】缺少参数，nickname:[{nickname}]，aweme_id:[{aweme_id}]，content:[{content[:30]}]")
            return
        title = f"【抖音】【{nickname}】发视频了"
        content = content[:100] + (content[100:] and "...")
        super().push(title, content, video_url, pic_url, extend_data={'dynamic_raw_data': dynamic_raw_data})

    def push_for_douyin_live(self, nickname=None, jump_url=None, room_title=None, room_cover_url=None, avatar_url=None):
        """
        抖音直播提醒推送
        :param nickname: 作者名
        :param jump_url: 跳转地址
        :param room_title: 直播间标题
        :param room_cover_url: 直播间封面
        :param avatar_url: 头像url
        """
        title = f"【抖音】【{nickname}】开播了"
        extend_data = {
            'avatar_url': avatar_url,
        }
        super().push(title, room_title, jump_url, room_cover_url, extend_data=extend_data)
