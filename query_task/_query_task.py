from collections import deque

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

        self.len_of_deque = 20
        self.dynamic_dict = {}
        self.living_status_dict = {}

    def query(self):
        raise NotImplementedError("Subclasses must implement the query method")

    def handle_for_result_null(self, null_id="-1", dict_key=None, module_name="未指定", user_name=None):
        """
        对动态状态请求返回为空时进行特殊处理
        :param null_id: 用于占位的id
        :param dict_key: dynamic_dict的key，通常为用户id
        :param module_name: 用于日志输出的模块名
        :param user_name: 用于日志输出的用户名或id
        """
        if dict_key is None:
            log.error(f"{module_name}，handle_for_result_null，参数dynamic_dict_key不能为空")
        if user_name is None:
            user_name = dict_key

        if self.dynamic_dict.get(dict_key, None) is None:
            # 当 dynamic_dict 中无 dict_key 时，证明是第一次请求且用户没发布过动态，进行初始化
            self.dynamic_dict[dict_key] = deque(maxlen=self.len_of_deque)
            self.dynamic_dict[dict_key].append(null_id)
            log.info(f"【{module_name}-查询动态状态-{self.name}】【{user_name}】动态初始化：{self.dynamic_dict[dict_key]}")
        else:
            # 当 dynamic_dict 中有 dict_key 时，检测 deque 的第一个元素是不是 null_id
            previous_id = self.dynamic_dict[dict_key].pop()
            self.dynamic_dict[dict_key].append(previous_id)
            if previous_id != null_id:
                # 当第一个元素不是 null_id 时，代表用户已经发布过动态了，此时可能是请求被拦截；否则代表用户持续没有发布动态
                log.error(f"【{module_name}-查询动态状态-{self.name}】【{user_name}】动态列表为空")

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        for item in self.target_push_name_list:
            target_push_channel = push_channel.push_channel_dict.get(item, None)
            if target_push_channel is None:
                log.error(f"【{self.name}】推送通道【{item}】不存在")
            else:
                try:
                    if extend_data is None:
                        extend_data = {}
                    extend_data = {
                        **extend_data,
                        'query_task_config': {
                            'name': self.name,
                            'enable': self.enable,
                            'type': self.type,
                            'intervals_second': self.intervals_second,
                            'begin_time': self.begin_time,
                            'end_time': self.end_time,
                            'target_push_name_list': self.target_push_name_list,
                            'enable_dynamic_check': self.enable_dynamic_check,
                            'enable_living_check': self.enable_living_check,
                        },
                    }
                    target_push_channel.push(title, content, jump_url, pic_url, extend_data)
                except Exception as e:
                    log.error(f"【{self.name}】推送通道【{item}】出错：{e}", exc_info=True)
