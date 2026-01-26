import json

from common import util
from common.logger import log
from . import PushChannel


class QQBot(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.base_url = str(config.get("base_url", ""))
        self.app_id = str(config.get("app_id", ""))
        self.app_secret = str(config.get("app_secret", ""))
        self.push_target_list = config.get("push_target_list", [])
        if self.base_url == "" or self.app_id == "" or self.app_secret == "" or len(self.push_target_list) == 0:
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")
            return
        # 初始化目标频道
        self.channel_id_name_dict = {}
        for guild_id, guild_name in self.init_guild_id_name_dict().items():
            self.init_channels(guild_id, guild_name)
        if len(self.channel_id_name_dict) == 0:
            log.error(f"【推送_{self.name}】未找到推送目标频道，推送功能将无法正常使用")

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        for channel_id, channel_name in self.channel_id_name_dict.items():
            push_url = f'/channels/{channel_id}/messages'
            headers = {
                "Content-Type": "application/json",
            }
            headers.update(self.get_headers())
            body = {
                "content": title + "\n\n" + content,
            }

            if pic_url is not None:
                body["content"] += '\n\n'
                body["image"] = pic_url

            response = util.requests_post(self.base_url + push_url, self.name, headers=headers, data=json.dumps(body))
            push_result = "成功" if util.check_response_is_ok(response) else "失败"
            log.info(f"【推送_{self.name}】【{channel_name}】{push_result}")

    def get_headers(self):
        response = util.requests_post("https://bots.qq.com/app/getAppAccessToken", f"{self.name}_获取accessToken", headers={
            "Content-Type": "application/json",
        }, data=json.dumps({
            "appId": self.app_id,
            "clientSecret": self.app_secret
        }))
        if util.check_response_is_ok(response):
            result = json.loads(str(response.content, "utf-8"))
            return {
                "Authorization": f"QQBot {result['access_token']}"
            }
        return {}

    # region 初始化参数

    def init_guild_id_name_dict(self) -> dict:
        guild_name_list = [str(item['guild_name']) for item in self.push_target_list]
        guild_id_name_dict = {}

        url = '/users/@me/guilds'
        response = util.requests_get(self.base_url + url, f"{self.name}_获取频道列表", headers=self.get_headers())
        if util.check_response_is_ok(response):
            result = json.loads(str(response.content, "utf-8"))
            for item in result:
                if item['name'] in guild_name_list:
                    guild_id_name_dict[item['id']] = item['name']
        return guild_id_name_dict

    def init_channels(self, guild_id, guild_name):
        channel_name_list = [
            str(channel)
            for item in self.push_target_list
            if item['guild_name'] == guild_name
            for channel in item['channel_name_list']
        ]

        url = f'/guilds/{guild_id}/channels'
        response = util.requests_get(self.base_url + url, f"{self.name}_获取子频道列表", headers=self.get_headers())
        if util.check_response_is_ok(response):
            result = json.loads(str(response.content, "utf-8"))
            for item in result:
                if item['name'] in channel_name_list and item['type'] == 0:  # 只获取文字子频道 https://bot.q.qq.com/wiki/develop/api/openapi/channel/model.html#channeltype
                    self.channel_id_name_dict[item['id']] = f'{guild_name}->{item["name"]}'

    # endregion
