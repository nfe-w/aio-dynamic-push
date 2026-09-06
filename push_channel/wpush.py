from common import util
from common.logger import log
from . import PushChannel


class WPush(PushChannel):
    """WPUSH 多渠道消息推送。文档：https://wpush.cn/docs"""

    def __init__(self, config):
        super().__init__(config)
        self.apikey = str(config.get("apikey", ""))
        self.channel = str(config.get("channel", "wechat") or "wechat")
        self.topic_code = str(config.get("topic_code", "") or "")
        if self.apikey == "":
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        if self.apikey == "":
            log.warning(f"【推送_{self.name}】apikey 为空，跳过推送")
            return

        desp = content
        if jump_url:
            desp = f"{desp}\n\n[点我直达]({jump_url})"
        if pic_url:
            desp = f"{desp}\n\n![]({pic_url})"

        body = {
            "apikey": self.apikey,
            "title": title,
            "content": desp,
            "channel": self.channel,
        }
        if self.topic_code:
            body["topic_code"] = self.topic_code

        headers = {"Content-Type": "application/json"}
        response = util.requests_post(
            "https://api.wpush.cn/api/v1/send",
            self.name,
            headers=headers,
            json=body,
        )
        ok = False
        if util.check_response_is_ok(response):
            try:
                data = response.json()
                ok = data.get("code") == 0
                if not ok:
                    log.error(
                        f"【推送_{self.name}】失败：{data.get('message') or data}"
                    )
            except Exception as e:
                log.error(f"【推送_{self.name}】解析响应失败：{e}")
        push_result = "成功" if ok else "失败"
        log.info(f"【推送_{self.name}】{push_result}")
