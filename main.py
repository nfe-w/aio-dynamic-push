import time

import schedule

import push_channel
import query_task
from common.config import global_config
from common.logger import log


def init_push_channel(push_channel_config_list: list):
    log.info("开始初始化推送通道")
    for config in push_channel_config_list:
        if config.get('enable', False):
            if push_channel.push_channel_dict.get(config.get('name', '')) is not None:
                raise ValueError(f"推送通道名称重复: {config.get('name', '')}")

            push_channel.push_channel_dict[config.get('name', '')] = push_channel.get_push_channel(config)
            log.info(f"初始化推送通道: {config.get('name', '')}，通道类型: {config.get('type', None)}")


def init_query_task(query_task_config_list: list):
    log.info("初始化查询任务")
    for config in query_task_config_list:
        if config.get('enable', False):
            schedule.every(config.get("intervals_second", 60)).seconds.do(query_task.get_query_task(config).query)
            log.info(f"初始化查询任务: {config.get('name', '')}，任务类型: {config.get('type', None)}")

    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    query_task_config_list = global_config.get_query_task_config()
    push_channel_config_list = global_config.get_push_channel_config()
    # 初始化推送通道
    init_push_channel(push_channel_config_list)
    # 初始化查询任务
    init_query_task(query_task_config_list)


if __name__ == '__main__':
    main()
