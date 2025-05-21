FROM python:3.9-alpine AS builder
COPY --from=ghcr.io/astral-sh/uv:0.7.6 /uv /uvx /bin/
WORKDIR /app
COPY . /app/
RUN uv sync --locked


FROM python:3.9-alpine

# 设置容器的时区为中国北京时间
ENV TZ=Asia/Shanghai

WORKDIR /app

COPY . /app/

COPY --from=builder /app/.venv /app/.venv

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
