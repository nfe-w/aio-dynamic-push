FROM python:3.9-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.7.6 /uv /uvx /bin/
WORKDIR /app
COPY . /app/
RUN uv sync --locked


FROM python:3.9-slim

# 设置容器的时区为中国北京时间
ENV TZ=Asia/Shanghai

# Install Node.js, npm, and Cypress dependencies in one layer
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    ca-certificates \
    dbus-x11 \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get install -y \
    libgtk2.0-0 \
    libgtk-3-0 \
    libgbm-dev \
    libnotify-dev \
    libnss3 \
    libxss1 \
    libasound2 \
    libxtst6 \
    xauth \
    xvfb \
    fonts-liberation \
    libappindicator3-1 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo-gobject2 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app/

COPY --from=builder /app/.venv /app/.venv

# Set environment variables for Cypress in Docker
ENV CYPRESS_CACHE_FOLDER=/root/.cache/Cypress
ENV DISPLAY=:99
ENV ELECTRON_DISABLE_SANDBOX=1
ENV CYPRESS_RUN_BINARY=/root/.cache/Cypress/13.17.0/Cypress/Cypress

# Install npm dependencies (including Cypress)
RUN npm install

# Install Cypress binary
RUN npx cypress install

# Skip verification during build - will verify at runtime with Xvfb
# RUN npx cypress verify

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
