import json

from common import util
from common.logger import log
from . import PushChannel


class NapCatQQ(PushChannel):
    """
    Author: https://github.com/YingChengxi
    See: https://github.com/nfe-w/aio-dynamic-push/issues/50
    """

    def __init__(self, config):
        super().__init__(config)
        self.api_url = str(config.get("api_url", ""))
        self.token = str(config.get("token", ""))
        _user_id = config.get("user_id", None)
        self.user_id = str(_user_id) if _user_id else None
        _group_id = config.get("group_id", None)
        self.group_id = str(_group_id) if _group_id else None
        if not self.api_url or (not self.user_id and not self.group_id):
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")
        if self.user_id and self.group_id:
            log.error(f"【推送_{self.name}】配置错误，不能同时设置 user_id 和 group_id")

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        message = [{
            "type": "text",
            "data": {"text": f"{title}\n\n{content}"}
        }]

        if pic_url:
            message.append({
                "type": "text",
                "data": {"text": "\n\n"}
            })
            message.append({
                "type": "image",
                "data": {"file": pic_url}
            })

        if jump_url:
            message.append({
                "type": "text",
                "data": {"text": f"\n\n原文: {jump_url}"}
            })

        payload = {
            "user_id": self.user_id,
            "group_id": self.group_id,
            "message": message
        }
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        api_endpoint = f"{self.api_url.rstrip('/')}/send_msg"

        try:
            response = util.requests_post(
                api_endpoint,
                self.name,
                headers=headers,
                data=json.dumps(payload)
            )

            if util.check_response_is_ok(response):
                resp_data = response.json()
                if resp_data.get("status") == "ok" and resp_data.get("retcode") == 0:
                    log.info(f"【推送_{self.name}】消息发送成功")
                    return True
                else:
                    error_msg = resp_data.get("message", "未知错误")
                    log.error(f"【推送_{self.name}】API返回错误: {error_msg}")
            else:
                log.error(f"【推送_{self.name}】请求失败，状态码: {response.status_code}")

        except Exception as e:
            log.error(f"【推送_{self.name}】发送消息时出现异常: {str(e)}")
            return False

        return False
