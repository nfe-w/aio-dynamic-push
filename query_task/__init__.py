from ._query_task import QueryTask
from .query_bilibili import QueryBilibili
from .query_demo import QueryDemo
from .query_douyin import QueryDouyin
from .query_douyu import QueryDouyu
from .query_weibo import QueryWeibo
from .query_xhs import QueryXhs


def get_query_task(config) -> QueryTask:
    task_type = config.get("type", None)
    if task_type == "bilibili":
        return QueryBilibili(config)
    if task_type == "weibo":
        return QueryWeibo(config)
    if task_type == "xhs":
        return QueryXhs(config)
    if task_type == "douyin":
        return QueryDouyin(config)
    if task_type == "douyu":
        return QueryDouyu(config)
    if task_type == "demo":
        return QueryDemo(config)

    raise ValueError(f"不支持的查询任务: {task_type}")
