from common import util
from common.logger import log
from . import PushChannel


class Bark(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.key = str(config.get("key", ""))

    def push(self, title, content, jump_url=None, pic_url=None):
        push_url = f"https://api.day.app/{self.key}/{title}/{content}?url={jump_url}"
        response = util.requests_post(push_url, self.name)
        push_result = "成功" if util.check_response_is_ok(response) else "失败"
        log.info(f"【推送_{self.name}】{push_result}")
