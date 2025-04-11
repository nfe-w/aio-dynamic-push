from abc import ABC, abstractmethod


class PushChannel(ABC):
    def __init__(self, config):
        self.name = config.get("name", "")
        self.enable = config.get("enable", False)
        self.type = config.get("type", "")

    @abstractmethod
    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        """
        :param title: 标题
        :param content: 内容
        :param jump_url: 跳转url
        :param pic_url: 图片url
        :param extend_data: 扩展数据
        """
        raise NotImplementedError("Subclasses must implement the push method")
