import json

from common import util
from common.logger import log
from . import PushChannel


class DingtalkBot(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.access_token = str(config.get("access_token", ""))
        if self.access_token == "":
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")

    def push(self, title, content, jump_url=None, pic_url=None):
        push_url = "https://oapi.dingtalk.com/robot/send"
        headers = {
            "Content-Type": "application/json"
        }
        params = {
            "access_token": self.access_token
        }
        body = {
            "msgtype": "link",
            "link": {
                "title": title,
                "text": content,
                "messageUrl": jump_url
            }
        }

        if pic_url is not None:
            body["link"]["picUrl"] = pic_url

        response = util.requests_post(push_url, self.name, headers=headers, params=params, data=json.dumps(body))
        push_result = "成功" if util.check_response_is_ok(response) else "失败"
        log.info(f"【推送_{self.name}】{push_result}")
