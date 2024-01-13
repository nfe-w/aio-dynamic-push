import os

import yaml

from common.logger import log


class ConfigReaderForYml(object):
    def __init__(self, config_file_name="config.yml"):
        config_file_path = os.path.join(os.getcwd(), config_file_name)
        if not os.path.exists(config_file_path):
            raise FileNotFoundError(f"No such file: {config_file_name}")
        with open(config_file_path, "r", encoding="utf-8") as file:
            self._config = yaml.safe_load(file)

    def get_common_config(self) -> dict:
        result = self._config.get("common", {})
        log.info(f"加载配置common: {result}")
        return result

    def get_query_task_config(self) -> list:
        result = self._config.get("query_task", [])
        log.info(f"加载配置query_task: {result}")
        return result

    def get_push_channel_config(self) -> list:
        result = self._config.get("push_channel", [])
        log.info(f"加载配置push_channel: {result}")
        return result


global_config = ConfigReaderForYml()
