from ._query_task import QueryTask
from .query_bilibili import QueryBilibili
from .query_douyin import QueryDouyin
from .query_weibo import QueryWeibo
from .query_xhs import QueryXhs


def get_query_task(config):
    task_type = config.get("type", None)
    if task_type == "bilibili":
        return QueryBilibili(config)
    if task_type == "weibo":
        return QueryWeibo(config)
    if task_type == "xhs":
        return QueryXhs(config)
    if task_type == "douyin":
        return QueryDouyin(config)
    else:
        raise ValueError(f"不支持的查询任务: {task_type}")
