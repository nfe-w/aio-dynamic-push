from common import util
from common.logger import log
from . import PushChannel


class ServerChan3(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.send_key = str(config.get("send_key", ""))
        self.uid = str(config.get("uid", ""))
        self.tags = config.get("tags", None)
        if self.send_key == "" or self.uid == "":
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        push_url = f"https://{self.uid}.push.ft07.com/send/{self.send_key}.send"
        data = {
            "title": title,
            "desp": f"{content}\n\n[点我直达]({jump_url})"
        }
        if pic_url:
            data["desp"] += f"\n\n![]({pic_url})"
        if self.tags:
            data["tags"] = self.tags
        response = util.requests_post(push_url, self.name, data=data)
        push_result = "成功" if util.check_response_is_ok(response) else "失败"
        log.info(f"【推送_{self.name}】{push_result}")
