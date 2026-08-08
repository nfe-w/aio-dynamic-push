from urllib.parse import quote
from common import util
from common.logger import log
from . import PushChannel


class Webhook(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.webhook_url = str(config.get("webhook_url", ""))
        self.request_method = str(config.get("request_method", "GET")).upper()
        if self.webhook_url == "":
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        if not self.webhook_url:
            log.warning(f"【推送_{self.name}】推送地址为空，跳过推送")
            return
        if self.request_method == "GET":
            safe_title = quote(str(title))
            safe_content = quote(str(content))
            safe_jump = quote(str(jump_url))
            safe_pic = quote(str(pic_url))
            push_url = (self.webhook_url
                        .replace("{{title}}", safe_title)
                        .replace("{{content}}", safe_content)
                        .replace("{{jump_url}}", safe_jump)
                        .replace("{{pic_url}}", safe_pic))
            response = util.requests_get(push_url, self.name)
        elif self.request_method == "POST":
            payload = extend_data.copy() if extend_data else {}
            payload["query_task_data"] = {
                "title": title,
                "content": content,
                "jump_url": jump_url,
                "pic_url": pic_url,
            }
            response = util.requests_post(self.webhook_url, self.name, json=payload)
        else:
            log.error(f"【推送_{self.name}】不支持的请求方法：{self.request_method}")
            return
        push_result = "成功" if util.check_response_is_ok(response) else "失败"
        log.info(f"【推送_{self.name}】{push_result}")
