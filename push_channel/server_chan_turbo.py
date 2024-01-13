from common import util
from common.logger import log
from . import PushChannel


class ServerChanTurbo(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.send_key = str(config.get("send_key", ""))

    def push(self, title, content, jump_url=None, pic_url=None):
        push_url = f"https://sctapi.ftqq.com/{self.send_key}.send"
        response = util.requests_post(push_url, self.name, params={"title": title, "desp": f"`{content}`[点我直达]({jump_url})"})
        push_result = "成功" if util.check_response_is_ok(response) else "失败"
        log.info(f"【推送_{self.name}】{push_result}")
