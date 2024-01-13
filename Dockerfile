FROM python:3.9-alpine

# 设置容器的时区为中国北京时间
ENV TZ=Asia/Shanghai

WORKDIR /app

COPY . /app/

RUN apk add --no-cache bash \
    && pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
