import json

from common import util
from common.logger import log
from . import PushChannel


class WeComApps(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.corp_id = str(config.get("corp_id", ""))
        self.agent_id = str(config.get("agent_id", ""))
        self.corp_secret = str(config.get("corp_secret", ""))
        if self.corp_id == "" or self.agent_id == "" or self.corp_secret == "":
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")

    def push(self, title, content, jump_url=None, pic_url=None):
        access_token = self._get_wechat_access_token()
        push_url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
        params = {
            "access_token": access_token
        }
        body = {
            "touser": "@all",
            "agentid": self.agent_id,
            "safe": 0,
            "enable_id_trans": 0,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800
        }

        if pic_url is None:
            body["msgtype"] = "textcard"
            body["textcard"] = {
                "title": title,
                "description": content,
                "url": jump_url,
                "btntxt": "打开详情"
            }
        else:
            body["msgtype"] = "news"
            body["news"] = {
                "articles": [
                    {
                        "title": title,
                        "description": content,
                        "url": jump_url,
                        "picurl": pic_url
                    }
                ]
            }

        response = util.requests_post(push_url, self.name, params=params, data=json.dumps(body))
        push_result = "成功" if util.check_response_is_ok(response) else "失败"
        log.info(f"【推送_{self.name}】{push_result}")

    def _get_wechat_access_token(self):
        access_token = None
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corp_id}&corpsecret={self.corp_secret}"
        response = util.requests_get(url, f"{self.name}_获取access_token")
        if util.check_response_is_ok(response):
            result = json.loads(str(response.content, "utf-8"))
            access_token = result["access_token"]
        return access_token
