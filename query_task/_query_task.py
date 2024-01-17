import push_channel
from common.logger import log


class QueryTask(object):
    def __init__(self, config):
        self.name = config.get("name", "")
        self.enable = config.get("enable", False)
        self.type = config.get("type", "")
        self.intervals_second = config.get("intervals_second", 60)
        self.begin_time = config.get("begin_time", "00:00")
        self.end_time = config.get("end_time", "23:59")
        self.target_push_name_list = config.get("target_push_name_list", [])
        self.enable_dynamic_check = config.get("enable_dynamic_check", False)
        self.enable_living_check = config.get("enable_living_check", False)

    def query(self):
        raise NotImplementedError("Subclasses must implement the query method")

    def push(self, title, content, jump_url=None, pic_url=None):
        for item in self.target_push_name_list:
            target_push_channel = push_channel.push_channel_dict.get(item, None)
            if target_push_channel is None:
                log.error(f"【{self.type}】推送通道【{item}】不存在")
            else:
                try:
                    target_push_channel.push(title, content, jump_url, pic_url)
                except Exception as e:
                    log.error(f"【{self.type}】推送通道【{item}】出错：{e}", exc_info=True)
