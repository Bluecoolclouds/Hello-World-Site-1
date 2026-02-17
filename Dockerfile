FROM node:20-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

RUN python3 -m venv /app/venv
RUN /app/venv/bin/pip install --no-cache-dir -r bot/requirements.txt

FROM node:20-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
COPY --from=builder /app/bot ./bot
COPY --from=builder /app/run_bot.py ./
COPY --from=builder /app/venv ./venv

RUN mkdir -p /app/data

ENV PATH="/app/venv/bin:$PATH"
ENV NODE_ENV=production
ENV PORT=5000
ENV BOT_DB_PATH=/app/data/bot.db

EXPOSE 5000

CMD ["node", "dist/index.cjs"]
