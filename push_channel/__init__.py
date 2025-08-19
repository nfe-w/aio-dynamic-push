from ._push_channel import PushChannel
from .bark import Bark
from .demo import Demo
from .dingtalk_bot import DingtalkBot
from .email import Email
from .feishu_apps import FeishuApps
from .feishu_bot import FeishuBot
from .gotify import Gotify
from .napcat_qq import NapCatQQ
from .qq_bot import QQBot
from .server_chan_3 import ServerChan3
from .server_chan_turbo import ServerChanTurbo
from .telegram_bot import TelegramBot
from .webhook import Webhook
from .wecom_apps import WeComApps
from .wecom_bot import WeComBot

push_channel_dict: dict[str, PushChannel] = {}

_channel_type_to_class = {
    "serverChan_turbo": ServerChanTurbo,
    "serverChan_3": ServerChan3,
    "wecom_apps": WeComApps,
    "wecom_bot": WeComBot,
    "dingtalk_bot": DingtalkBot,
    "feishu_apps": FeishuApps,
    "feishu_bot": FeishuBot,
    "telegram_bot": TelegramBot,
    "qq_bot": QQBot,
    "napcat_qq": NapCatQQ,
    "bark": Bark,
    "gotify": Gotify,
    "webhook": Webhook,
    "email": Email,
    "demo": Demo,
}


def get_push_channel(config) -> PushChannel:
    channel_type = config.get("type", None)
    if channel_type is None or channel_type not in _channel_type_to_class:
        raise ValueError(f"不支持的通道类型: {channel_type}")

    return _channel_type_to_class[channel_type](config)
