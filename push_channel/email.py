import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from common.logger import log
from . import PushChannel


class Email(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        self.smtp_host = str(config.get("smtp_host", ""))
        self.smtp_port = str(config.get("smtp_port", ""))
        self.smtp_ssl = config.get("smtp_ssl", True)
        self.smtp_tls = config.get("smtp_tls", False)
        self.sender_email = str(config.get("sender_email", ""))
        self.sender_password = str(config.get("sender_password", ""))
        self.receiver_email = str(config.get("receiver_email", ""))
        if self.smtp_host == "" or self.smtp_port == "" or self.sender_email == "" or self.sender_password == "" or self.receiver_email == "":
            log.error(f"【推送_{self.name}】配置不完整，推送功能将无法正常使用")

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        message = MIMEMultipart()
        message["Subject"] = title
        message["From"] = self.sender_email
        message["To"] = self.receiver_email

        body = f"{content}<br><a href='{jump_url}'>点击查看详情</a>"
        if pic_url is not None:
            body += f"<br><img src='{pic_url}'>"
        message.attach(MIMEText(body, "html"))

        try:
            func = smtplib.SMTP_SSL if self.smtp_ssl else smtplib.SMTP
            with func(self.smtp_host, int(self.smtp_port)) as server:
                if self.smtp_tls:
                    server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.receiver_email, message.as_string())
                push_result = "成功"
        except smtplib.SMTPException as e:
            log.error(f"【推送_{self.name}】{e}", exc_info=True)
            push_result = "失败"
        log.info(f"【推送_{self.name}】{push_result}")
