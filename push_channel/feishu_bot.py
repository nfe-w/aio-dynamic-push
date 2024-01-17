import json

from common import util
from common.logger import log
from . import PushChannel


class FeishuBot(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.webhook_key = str(config.get("webhook_key", ""))
        if self.webhook_key == "":
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")

    def push(self, title, content, jump_url=None, pic_url=None):
        push_url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{self.webhook_key}"
        headers = {
            "Content-Type": "application/json"
        }
        card_elements = [
            {
                "tag": "markdown",
                "content": content
            }
        ]
        if pic_url is not None:
            img_key = self._get_img_key(pic_url)
            if img_key is not None:
                card_elements.append({
                    "alt": {
                        "content": "",
                        "tag": "plain_text"
                    },
                    "img_key": img_key,
                    "tag": "img"
                })
        card_elements.append({
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {
                        "tag": "plain_text",
                        "content": "点我跳转"
                    },
                    "type": "primary",
                    "url": jump_url
                }
            ]
        })
        body = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "template": "blue",
                    "title": {
                        "content": title,
                        "tag": "plain_text"
                    }
                },
                "elements": card_elements
            }
        }

        response = util.requests_post(push_url, self.name, headers=headers, data=json.dumps(body))
        push_result = "成功" if util.check_response_is_ok(response) else "失败"
        log.info(f"【推送_{self.name}】{push_result}")

    def _get_img_key(self, pic_url: str) -> str:
        # todo: 上传图片到飞书
        return None
