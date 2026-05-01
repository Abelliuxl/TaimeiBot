#!/bin/bash
pkill -f "uv run python"
sleep 2
cd /home/liuxl/TaimeiBot
nohup uv run python main.py > /home/liuxl/TaimeiBot/logs/restart_bot.log 2>&1 &
