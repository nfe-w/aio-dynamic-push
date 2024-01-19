import time

from common.logger import log
from common.proxy import my_proxy
from query_task import QueryTask


class QueryDemo(QueryTask):
    def __init__(self, config):
        super().__init__(config)
        # 在这里初始化任务需要的参数
        self.uid_list = config.get("uid_list", [])

    def query(self):
        if not self.enable:
            return
        try:
            current_time = time.strftime("%H:%M", time.localtime(time.time()))
            if self.begin_time <= current_time <= self.end_time:
                my_proxy.current_proxy_ip = my_proxy.get_proxy(proxy_check_url="用于检测代理是否可用的url")
                if self.enable_dynamic_check:
                    for uid in self.uid_list:
                        self.query_dynamic(uid)
        except Exception as e:
            log.error(f"【XXX-查询任务-{self.name}】出错：{e}", exc_info=True)

    def query_dynamic(self, uid=None):
        if uid is None:
            return
        # 在这里实现检测逻辑，记得要在 query_task/__init__.py 中注册任务类型
        self.push_for_xxx(username="用户名", dynamic_id="动态id", content="动态内容", pic_url="图片地址", jump_url="跳转地址", dynamic_time="动态发送时间")

    def push_for_xxx(self, username=None, dynamic_id=None, content=None, pic_url=None, jump_url=None, dynamic_time=None):
        """
        XXX动态提醒推送
        :param username: 用户名
        :param dynamic_id: 动态id
        :param content: 动态内容
        :param pic_url: 图片地址
        :param jump_url: 跳转地址
        :param dynamic_time: 动态发送时间
        """
        if username is None or dynamic_id is None or content is None:
            log.error(f"【XXX-动态提醒推送-{self.name}】缺少参数，username:[{username}]，dynamic_id:[{dynamic_id}]，content:[{content[:30]}]")
            return
        title = f"【XXX】【{username}】发动态"
        content = f"{content[:100] + (content[100:] and '...')}[{dynamic_time}]"
        super().push(title, content, jump_url, pic_url)
