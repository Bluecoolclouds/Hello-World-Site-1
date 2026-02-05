#!/bin/bash

echo "Starting Telegram Bot in background..."
python3 run_bot.py &
BOT_PID=$!

echo "Starting Web Application..."
npm run dev

# Kill bot when web app stops
kill $BOT_PID 2>/dev/null
