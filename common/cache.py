from common.logger import log

local_cache = {}


def set_cached_value(key, value):
    log.info(f"[本地缓存]将: {key} -> {value} 存入缓存中")
    local_cache[key] = value


def get_cached_value(key, need_log=False):
    value = local_cache.get(key)
    if need_log is True:
        log.info(f"[本地缓存]从缓存中获取: {key} -> {value}")
    return value
