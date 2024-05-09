import json

from common import util
from common.logger import log
from . import PushChannel


class TelegramBot(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.api_token = str(config.get("api_token", ""))
        self.chat_id = str(config.get("chat_id", ""))
        if self.api_token == "" or self.chat_id == "":
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        push_url = f"https://api.telegram.org/bot{self.api_token}/sendMessage"
        headers = {
            "Content-Type": "application/json"
        }
        body = {
            "chat_id": self.chat_id,
            "text": f"[{title}]({jump_url})\n`{content}`",
            "parse_mode": "Markdown"
        }
        if pic_url is not None:
            body["link_preview_options"] = {
                "is_disabled": False,
                "url": pic_url
            }
        response = util.requests_post(push_url, self.name, headers=headers, data=json.dumps(body))
        push_result = "成功" if util.check_response_is_ok(response) else "失败"
        log.info(f"【推送_{self.name}】{push_result}")
