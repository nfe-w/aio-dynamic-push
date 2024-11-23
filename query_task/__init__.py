from ._query_task import QueryTask
from .query_bilibili import QueryBilibili
from .query_demo import QueryDemo
from .query_douyin import QueryDouyin
from .query_douyu import QueryDouyu
from .query_huya import QueryHuya
from .query_weibo import QueryWeibo
from .query_xhs import QueryXhs

_task_type_to_class = {
    "bilibili": QueryBilibili,
    "weibo": QueryWeibo,
    "xhs": QueryXhs,
    "douyin": QueryDouyin,
    "douyu": QueryDouyu,
    "huya": QueryHuya,
    "demo": QueryDemo,
}


def get_query_task(config) -> QueryTask:
    task_type = config.get("type", None)
    if task_type is None or task_type not in _task_type_to_class:
        raise ValueError(f"不支持的查询任务: {task_type}")

    return _task_type_to_class[task_type](config)
