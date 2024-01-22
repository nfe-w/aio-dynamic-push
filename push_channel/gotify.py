import json

from common import util
from common.logger import log
from . import PushChannel


class Gotify(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.web_server_url = str(config.get("web_server_url", ""))
        if self.web_server_url == "":
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")

    def push(self, title, content, jump_url=None, pic_url=None):
        headers = {
            "Content-Type": "application/json",
        }
        body = {
            "title": title,
            "message": content,
            "priority": 5
        }
        response = util.requests_post(self.web_server_url, self.name, headers=headers, data=json.dumps(body))
        push_result = "成功" if util.check_response_is_ok(response) else "失败"
        log.info(f"【推送_{self.name}】{push_result}")
