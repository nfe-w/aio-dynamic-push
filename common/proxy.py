import requests

from common.config import global_config
from common.logger import log


class Proxy(object):
    current_proxy_ip = None

    _enable = False
    _proxy_pool_url = None

    def __init__(self):
        common_config = global_config.get_common_config()
        proxy_pool = common_config.get("proxy_pool", None)
        if proxy_pool is not None:
            self._enable = proxy_pool.get("enable", False)
            self._proxy_pool_url = proxy_pool.get("proxy_pool_url", None)
            if self._enable and self._proxy_pool_url is None:
                self._enable = False
                log.error("【ip池】未配置ip池地址")
            if self._enable:
                log.info(f"【ip池】已启用，地址: {self._proxy_pool_url}")

    def get_proxy(self, proxy_check_url="https://www.baidu.com", timeout=2, retry_count=10):
        """
        获取一个有效的代理ip
        :param proxy_check_url: 检验代理ip有效性的url
        :param timeout: 超时时间
        :param retry_count: 重试次数
        :return: 有效的代理ip
        """
        if not self._enable:
            return None

        while retry_count > 0:
            # noinspection PyBroadException
            try:
                ip_pool_response = requests.get(self._proxy_pool_url + "/get")
            except Exception:
                log.error("【ip池】连接失败")
                return None

            proxy_ip = ip_pool_response.json().get("proxy", None)
            if proxy_ip is None:
                log.info("【ip池】当前为空池")
                return None

            proxies = {
                "http": f"http://{proxy_ip}",
                "https": f"http://{proxy_ip}",
            }
            # noinspection PyBroadException
            try:
                response = requests.get(proxy_check_url, proxies=proxies, timeout=timeout)
                if response.status_code == requests.codes.OK:
                    log.info(f"【ip池】获取ip成功: {proxy_ip}")
                    return proxy_ip
            except ConnectionRefusedError:
                retry_count -= 1
                self._delete_proxy(proxy_ip)
            except Exception:
                retry_count -= 1
        log.info(f"【ip池】尝试多次均未获取到有效ip")
        return None

    def _delete_proxy(self, proxy_ip):
        requests.get(self._proxy_pool_url + f"/delete/?proxy={proxy_ip}")
        log.info(f"【ip池】移除ip: {proxy_ip}")


my_proxy = Proxy()
