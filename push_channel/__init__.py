from ._push_channel import PushChannel
from .bark import Bark
from .demo import Demo
from .dingtalk_bot import DingtalkBot
from .email import Email
from .feishu_apps import FeishuApps
from .feishu_bot import FeishuBot
from .gotify import Gotify
from .server_chan_turbo import ServerChanTurbo
from .telegram_bot import TelegramBot
from .webhook import Webhook
from .wecom_apps import WeComApps
from .wecom_bot import WeComBot

push_channel_dict: dict[str, PushChannel] = {}


def get_push_channel(config) -> PushChannel:
    channel_type = config.get("type", None)
    if channel_type == "serverChan_turbo":
        return ServerChanTurbo(config)
    if channel_type == "wecom_apps":
        return WeComApps(config)
    if channel_type == "wecom_bot":
        return WeComBot(config)
    if channel_type == "dingtalk_bot":
        return DingtalkBot(config)
    if channel_type == "feishu_apps":
        return FeishuApps(config)
    if channel_type == "feishu_bot":
        return FeishuBot(config)
    if channel_type == "telegram_bot":
        return TelegramBot(config)
    if channel_type == "bark":
        return Bark(config)
    if channel_type == "gotify":
        return Gotify(config)
    if channel_type == "webhook":
        return Webhook(config)
    if channel_type == "email":
        return Email(config)
    if channel_type == "demo":
        return Demo(config)

    raise ValueError(f"不支持的通道类型: {channel_type}")
