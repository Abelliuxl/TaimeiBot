#!/bin/bash
# 通用 supervisord 管理命令别名 - 适用于任何项目

# 基础命令别名
sup_status() {
    if [ -n "$1" ]; then
        supervisorctl -c supervisord.conf status "$1"
    else
        supervisorctl -c supervisord.conf status
    fi
}

sup_start() {
    if [ -n "$1" ]; then
        supervisorctl -c supervisord.conf start "$1"
    else
        echo "请指定要启动的服务名称"
        echo "用法: sup_start <服务名>"
    fi
}

sup_stop() {
    if [ -n "$1" ]; then
        supervisorctl -c supervisord.conf stop "$1"
    else
        echo "请指定要停止的服务名称"
        echo "用法: sup_stop <服务名>"
    fi
}

sup_restart() {
    if [ -n "$1" ]; then
        supervisorctl -c supervisord.conf restart "$1"
    else
        echo "请指定要重启的服务名称"
        echo "用法: sup_restart <服务名>"
    fi
}

# 日志查看函数
sup_log() {
    if [ -n "$1" ]; then
        supervisorctl -c supervisord.conf tail "$1"
    else
        echo "请指定要查看日志的服务名称"
        echo "用法: sup_log <服务名>"
    fi
}

sup_logf() {
    if [ -n "$1" ]; then
        supervisorctl -c supervisord.conf tail -f "$1"
    else
        echo "请指定要实时查看日志的服务名称"
        echo "用法: sup_logf <服务名>"
    fi
}

# supervisord本身管理
alias supdaemon_start='supervisord -c supervisord.conf'
alias supdaemon_stop='supervisorctl -c supervisord.conf shutdown'
alias supdaemon_reload='supervisorctl -c supervisord.conf reload'
alias supdaemon_status='supervisorctl -c supervisord.conf status'

# 快速查看所有服务状态
sup_all() {
    echo "=== 所有服务状态 ==="
    supervisorctl -c supervisord.conf status
}

# 快速重启所有服务
sup_restart_all() {
    echo "正在重启所有服务..."
    supervisorctl -c supervisord.conf restart all
}

# 调试函数
sup_debug() {
    if [ -n "$1" ]; then
        echo "=== 服务 $1 状态 ==="
        supervisorctl -c supervisord.conf status "$1"
        echo -e "\n=== 最近日志 ==="
        supervisorctl -c supervisord.conf tail -n 10 "$1"
    else
        echo "请指定要调试的服务名称"
        echo "用法: sup_debug <服务名>"
    fi
}

# 查看特定服务的错误日志
sup_err() {
    if [ -n "$1" ]; then
        if [ -f "logs/$1.stderr.log" ]; then
            tail -f "logs/$1.stderr.log"
        else
            echo "错误日志文件不存在: logs/$1.stderr.log"
        fi
    else
        echo "请指定要查看错误日志的服务名称"
        echo "用法: sup_err <服务名>"
    fi
}

# 查看特定服务的输出日志
sup_out() {
    if [ -n "$1" ]; then
        if [ -f "logs/$1.stdout.log" ]; then
            tail -f "logs/$1.stdout.log"
        else
            echo "输出日志文件不存在: logs/$1.stdout.log"
        fi
    else
        echo "请指定要查看输出日志的服务名称"
        echo "用法: sup_out <服务名>"
    fi
}

# 帮助信息
sup_help() {
    echo "通用 supervisord 管理命令别名：
    
基础命令：
  sup_status [服务名]     - 查看服务状态（不指定服务名则显示所有）
  sup_start <服务名>      - 启动指定服务
  sup_stop <服务名>       - 停止指定服务
  sup_restart <服务名>    - 重启指定服务
  
日志查看：
  sup_log <服务名>        - 查看服务日志
  sup_logf <服务名>       - 实时查看服务日志
  sup_err <服务名>        - 实时查看错误日志
  sup_out <服务名>        - 实时查看输出日志
  
系统管理：
  supdaemon_start        - 启动supervisord
  supdaemon_stop         - 停止supervisord
  supdaemon_reload       - 重载supervisord配置
  supdaemon_status       - 查看supervisord状态
  
批量操作：
  sup_all                - 查看所有服务状态
  sup_restart_all        - 重启所有服务
  
调试：
  sup_debug <服务名>     - 查看服务调试信息
  
帮助：
  sup_help               - 显示此帮助信息
  
示例：
  sup_status taimeibot   - 查看taimeibot状态
  sup_logf myapp         - 实时查看myapp日志
  sup_restart nginx      - 重启nginx服务"
}

echo "通用 supervisord 管理别名已加载！使用 'sup_help' 查看所有可用命令。"
