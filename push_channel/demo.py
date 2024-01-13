from common.logger import log
from . import PushChannel


class Demo(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        # 在这里初始化通道需要的参数

    def push(self, title, content, jump_url=None, pic_url=None):
        # 在这里实现推送逻辑，记得要在 push_channel/__init__.py 中注册推送通道
        push_result = "成功"
        log.info(f"【推送_{self.name}】{push_result}")
