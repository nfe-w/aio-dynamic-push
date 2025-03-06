from urllib.parse import urlencode

from common import util
from common.logger import log
from . import PushChannel


class Bark(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.key = str(config.get("key", ""))
        if self.key == "":
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        push_url = f"https://api.day.app/{self.key}/{title}/{content}"

        params = {}
        if jump_url:
            params["url"] = jump_url

        if extend_data:
            query_task_config = extend_data.get("query_task_config")
            if query_task_config and "name" in query_task_config:
                params["group"] = query_task_config["name"]

        push_url = f"{push_url}?{urlencode(params)}" if params else push_url
        response = util.requests_post(push_url, self.name)
        push_result = "成功" if util.check_response_is_ok(response) else "失败"
        log.info(f"【推送_{self.name}】{push_result}")
