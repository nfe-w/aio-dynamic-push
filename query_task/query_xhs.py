import json
import time
from collections import deque

from bs4 import BeautifulSoup

from common import util
from common.logger import log
from common.proxy import my_proxy
from query_task import QueryTask


class QueryXhs(QueryTask):
    def __init__(self, config):
        super().__init__(config)
        self.profile_id_list = config.get("profile_id_list", [])
        self.cookie = config.get("cookie", "")

    def query(self):
        if not self.enable:
            return
        try:
            current_time = time.strftime("%H:%M", time.localtime(time.time()))
            if self.begin_time <= current_time <= self.end_time:
                my_proxy.current_proxy_ip = my_proxy.get_proxy(proxy_check_url="https://www.xiaohongshu.com/")
                if self.enable_dynamic_check:
                    for profile_id in self.profile_id_list:
                        self.query_dynamic(profile_id)
        except Exception as e:
            log.error(f"【小红书-查询任务-{self.name}】出错：{e}", exc_info=True)

    def query_dynamic(self, profile_id=None):
        if profile_id is None:
            return
        query_url = f"https://www.xiaohongshu.com/user/profile/{profile_id}"
        headers = self.get_headers()
        if self.cookie != "":
            headers["cookie"] = self.cookie
        response = util.requests_get(query_url, f"小红书-查询动态状态-{self.name}", headers=headers, use_proxy=True)
        if util.check_response_is_ok(response):
            html_text = response.text
            soup = BeautifulSoup(html_text, "html.parser")
            scripts = soup.findAll("script")
            result = None
            for script in scripts:
                if script.string is not None and "window.__INITIAL_STATE__=" in script.string:
                    try:
                        result = json.loads(script.string.replace("window.__INITIAL_STATE__=", "").replace("undefined", "null"))
                    except TypeError:
                        log.error(f"【小红书-查询动态状态-{self.name}】json解析错误，profile_id：{profile_id}")
                        return None
                    break

            if result is None:
                log.error(f"【小红书-查询动态状态-{self.name}】请求返回数据为空，profile_id：{profile_id}")
            else:
                user_name = result["user"]["userPageData"]["basicInfo"]["nickname"]

                avatar_url = None
                try:
                    avatar_url = result["user"]["userPageData"]["basicInfo"]["images"]
                except Exception:
                    log.error(f"【小红书-查询动态状态-{self.name}】头像获取发生错误，profile_id：{profile_id}")

                notes = result["user"]["notes"][0]
                if len(notes) == 0:
                    super().handle_for_result_null("-1", profile_id, "小红书", user_name)
                    return

                # 循环遍历 notes ，剔除不满足要求的数据
                notes = [note for note in notes if
                         note.get("noteCard") is not None  # 跳过不包含 noteCard 的数据
                         and (note["noteCard"].get("interactInfo") is None or note["noteCard"]["interactInfo"].get("sticky") is not True)  # 跳过置顶
                         ]

                # 跳过置顶后再判断一下，防止越界
                if len(notes) == 0:
                    super().handle_for_result_null("-1", profile_id, "小红书", user_name)
                    return

                note = notes[0]
                note_title = note["noteCard"]["displayTitle"]

                if self.dynamic_dict.get(profile_id, None) is None:
                    self.dynamic_dict[profile_id] = deque(maxlen=self.len_of_deque)
                    for index in range(self.len_of_deque):
                        if index < len(notes):
                            self.dynamic_dict[profile_id].appendleft(notes[index]["noteCard"]["displayTitle"])
                    log.info(f"【小红书-查询动态状态-{self.name}】【{user_name}】动态初始化：{self.dynamic_dict[profile_id]}")
                    return

                if note_title not in self.dynamic_dict[profile_id]:
                    previous_note_title = self.dynamic_dict[profile_id].pop()
                    self.dynamic_dict[profile_id].append(previous_note_title)
                    log.info(f"【小红书-查询动态状态-{self.name}】【{user_name}】上一条动态标题[{previous_note_title}]，本条动态标题[{note_title}]")
                    self.dynamic_dict[profile_id].append(note_title)
                    log.debug(self.dynamic_dict[profile_id])

                    note_title = note_title
                    note_desc = ''
                    dynamic_time = '无法获取内容，请打开小红书查看详情'

                    note_card = note["noteCard"]
                    content = f"【{note_title}】{note_desc}"
                    pic_url = note_card["cover"]["infoList"][-1]["url"]
                    jump_url = f"https://www.xiaohongshu.com/user/profile/{profile_id}"
                    log.info(f"【小红书-查询动态状态-{self.name}】【{user_name}】动态有更新，准备推送：{content[:30]}")
                    self.push_for_xhs_dynamic(user_name, note_title, content, pic_url, jump_url, dynamic_time, dynamic_raw_data=note, avatar_url=avatar_url)

    def get_note_detail(self, note_id=None):
        if note_id is None:
            return None
        query_url = f"https://www.xiaohongshu.com/explore/{note_id}"
        headers = self.get_headers()
        response = util.requests_get(query_url, f"小红书-查询动态明细-{self.name}", headers=headers, use_proxy=True)
        if util.check_response_is_ok(response):
            html_text = response.text
            soup = BeautifulSoup(html_text, "html.parser")
            scripts = soup.findAll("script")
            result = None
            for script in scripts:
                if script.string is not None and "window.__INITIAL_STATE__=" in script.string:
                    try:
                        result = json.loads(script.string.replace("window.__INITIAL_STATE__=", "").replace("undefined", "null"))
                    except TypeError:
                        log.error(f"【小红书-查询动态明细-{self.name}】json解析错误，note_id：{note_id}")
                        return None
                    break

            if result is None:
                log.error(f"【小红书-查询动态明细-{self.name}】请求返回数据为空，note_id：{note_id}")
            else:
                note = result["note"]
                if note is None:
                    return None
                return note["noteDetailMap"][note["firstNoteId"]]["note"]

    @staticmethod
    def get_headers():
        return {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "sec-ch-ua": "'Google Chrome';v='119', 'Chromium';v='119', 'Not?A_Brand';v='24'",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "'macOS'",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
        }

    def push_for_xhs_dynamic(self, username=None, note_title=None, content=None, pic_url=None, jump_url=None, dynamic_time=None, dynamic_raw_data=None, avatar_url=None):
        """
        小红书动态提醒推送
        :param username: 博主名
        :param note_title: 笔记标题
        :param content: 动态内容
        :param pic_url: 图片地址
        :param jump_url: 跳转地址
        :param dynamic_time: 动态发送时间
        :param dynamic_raw_data: 动态原始数据
        :param avatar_url: 头像url
        """
        if username is None or note_title is None or content is None:
            log.error(f"【小红书-动态提醒推送-{self.name}】缺少参数，username:[{username}]，note_title:[{note_title}]，content:[{content[:30]}]")
            return
        title = f"【小红书】【{username}】发动态了"
        content = f"{content[:100] + (content[100:] and '...')}[{dynamic_time}]"
        extend_data = {
            'dynamic_raw_data': dynamic_raw_data,
            'avatar_url': avatar_url,
        }
        super().push(title, content, jump_url, pic_url, extend_data=extend_data)
