class PushChannel(object):
    def __init__(self, config):
        self.name = config.get("name", "")
        self.enable = config.get("enable", False)
        self.type = config.get("type", "")

    def push(self, title, content, jump_url=None, pic_url=None):
        """
        :param title: 标题
        :param content: 内容
        :param jump_url: 跳转url
        :param pic_url: 图片url
        """
        raise NotImplementedError("Subclasses must implement the push method")
