#!/bin/bash
# 停止脚本
pkill -f "python main.py"
#sleep 60  # 等待1分钟
# 重新启动
cd /home/liuxl/TaimeiBot
nohup /home/liuxl/miniconda3/bin/python main.py > /home/liuxl/TaimeiBot/logs/restart_bot.log 2>&1 &
