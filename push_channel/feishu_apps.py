import json
import mimetypes
import os
import uuid

import requests
from requests_toolbelt import MultipartEncoder

from common import util
from common.logger import log
from . import PushChannel


class FeishuApps(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.app_id = str(config.get("app_id", ""))
        self.app_secret = str(config.get("app_secret", ""))
        self.receive_id_type = str(config.get("receive_id_type", ""))
        self.receive_id = str(config.get("receive_id", ""))
        if self.app_id == "" or self.app_secret == "" or self.receive_id_type == "" or self.receive_id == "":
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        tenant_access_token = self._get_tenant_access_token()
        if tenant_access_token is None:
            return None
        url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={self.receive_id_type}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {tenant_access_token}"
        }
        card_elements = [
            {
                "tag": "markdown",
                "content": content
            }
        ]
        if pic_url is not None:
            img_key = self._get_img_key(pic_url)
            if img_key is not None:
                card_elements.append({
                    "alt": {
                        "content": "",
                        "tag": "plain_text"
                    },
                    "img_key": img_key,
                    "tag": "img"
                })
        card_elements.append({
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {
                        "tag": "plain_text",
                        "content": "点我跳转"
                    },
                    "type": "primary",
                    "url": jump_url
                }
            ]
        })
        content = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "blue",
                "title": {
                    "content": title,
                    "tag": "plain_text"
                }
            },
            "elements": card_elements
        }
        body = {
            "receive_id": self.receive_id,
            "msg_type": "interactive",
            "content": json.dumps(content)
        }
        response = util.requests_post(url, self.name, headers=headers, data=json.dumps(body))
        push_result = "成功" if util.check_response_is_ok(response) else "失败"
        log.info(f"【推送_{self.name}】{push_result}")

    def _get_img_key(self, pic_url: str):
        # 下载图片
        log.info(f"【推送_{self.name}】开始下载图片：{pic_url}")
        response = requests.get(pic_url, verify=False)
        if not util.check_response_is_ok(response):
            log.error(f"【推送_{self.name}】下载图片{pic_url}失败")
            return None
        content_type = response.headers['Content-Type']
        extension = mimetypes.guess_extension(content_type)
        # 如果无法从内容类型推断扩展名，则默认使用.jpg
        if not extension:
            extension = '.jpg'
        file_path = str(uuid.uuid4()) + extension
        with open(file_path, 'wb') as file:
            file.write(response.content)
        log.info(f"【推送_{self.name}】下载图片{pic_url}成功")

        # 上传图片
        tenant_access_token = self._get_tenant_access_token()
        if tenant_access_token is None:
            # 删除本地文件
            os.remove(file_path)
            return None

        url = "https://open.feishu.cn/open-apis/im/v1/images"
        response = None
        try:
            # 使用上下文管理器确保文件在请求完成后被关闭
            with open(file_path, 'rb') as f:
                multi_form = MultipartEncoder({
                    'image_type': 'message',
                    # 同时传递文件名与内容类型，提升兼容性
                    'image': (f"image{extension}", f, content_type if content_type else 'application/octet-stream')
                })
                headers = {
                    'Authorization': f"Bearer {tenant_access_token}",
                    'Content-Type': multi_form.content_type,
                }
                response = util.requests_post(url, self.name, headers=headers, data=multi_form)
        finally:
            # 无论上传是否成功都尝试删除临时文件，避免文件句柄占用导致 WinError 32
            try:
                os.remove(file_path)
            except Exception as e:
                log.warning(f"【推送_{self.name}】删除临时图片失败：{file_path}，原因：{e}")

        if util.check_response_is_ok(response):
            return response.json()["data"]["image_key"]
        else:
            log.error(f"【推送_{self.name}】上传图片失败")
            return None

    def _get_tenant_access_token(self):
        url = f"https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        body = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        response = util.requests_post(url, self.name, headers=headers, data=json.dumps(body))
        if util.check_response_is_ok(response):
            return response.json()["tenant_access_token"]
        else:
            log.error(f"【推送_{self.name}】获取tenant_access_token失败")
            return None
