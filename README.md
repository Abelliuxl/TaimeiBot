# TaimeiBot Pro

TaimeiBot Pro 是一个基于 [khl.py](https://github.com/TWT233/khl.py) 开发的专业版开黑啦机器人，专注于魔兽世界游戏相关功能，提供天赋查询、翻译、AI对话等功能，并配备了强大的进程管理系统。

## 功能特性

### 1. 天赋查询 `/tf`
- 支持查询指定职业专精的天赋加点
- 从 raider.io 获取高分玩家的天赋数据
- 支持中英文职业名称和简写
- 示例：`/tf 惩戒骑` 或 `/tf ret`

### 2. AI对话 `/tm`
- 基于 DeepSeek Chat 的AI对话功能
- 模拟暴躁、专业的魔兽世界玩家风格
- 示例：`/tm 请问术士和法师哪个比较厉害？`

### 3. 自动翻译
- 在指定频道自动翻译中英文消息
- 支持中文转英文和英文转中文
- 翻译准确自然，无冗余内容

### 4. 消息管理
- `/send` 发送消息到指定频道
- `/dm` 发送私信给指定用户
- 支持@机器人进行对话

### 5. 专业进程管理系统 (v1.5新增)
- 基于supervisord的进程管理，确保7x24小时稳定运行
- 通用supervisord命令别名系统，可管理任何服务
- 自动重启机制，崩溃后自动恢复
- 完善的日志管理和监控工具
- 简化的运维命令，大幅提升管理效率

## 安装说明

1. 克隆项目并安装依赖：
```bash
git clone https://github.com/yourusername/TaimeiBot.git
cd TaimeiBot-1.5
pip install -r requirements.txt
```

2. 配置文件设置：
- 在 `config` 目录下创建 `config.json`：
```json
{
    "token": "你的机器人token",
    "openai_api2d_url": "API地址",
    "openai_api2d_api_key": "你的API密钥"
}
```
- 确保 `config` 目录下有以下文件：
  - `Abbreviations.json`：职业专精别名配置
  - `en_cn_wow.json`：魔兽世界中英文翻译

3. 配置玩家数据：
- 在 `raider_data` 目录下创建 `player_info.json`：
```json
[
    {
        "name": "角色名",
        "class": "职业",
        "spec": "专精",
        "region": "地区",
        "realm": "服务器"
    }
]
```

## 项目结构

```
TaimeiBot-1.5/
├── config/                 # 配置文件目录
│   ├── Abbreviations.json # 职业专精别名配置
│   ├── config.json        # 主配置文件
│   └── en_cn_wow.json    # 游戏术语翻译
├── handlers/              # 消息处理模块
│   └── message_handlers.py
├── services/             # 服务模块
│   ├── message_service.py
│   └── raider_service.py
├── utils/                # 工具模块
│   └── logging_utils.py
├── main.py              # 主程序入口
└── requirements.txt     # 项目依赖
```

## 使用说明

### 方式一：直接启动
```bash
python main.py
```

### 方式二：使用进程管理系统 (推荐)

1. 加载管理命令：
```bash
source supervisor_aliases.sh
```

2. 启动supervisord：
```bash
supdaemon_start
```

3. 管理机器人：
```bash
sup_status taimeibot        # 查看状态
sup_start taimeibot         # 启动机器人
sup_restart taimeibot       # 重启机器人
sup_logf taimeibot          # 实时查看日志
sup_debug taimeibot         # 调试信息
```

4. 批量操作：
```bash
sup_all                    # 查看所有服务状态
sup_restart_all            # 重启所有服务
```

## 机器人命令

- `/help` - 显示帮助信息
- `/ping` - 测试机器人是否在线
- `/tf <职业专精>` - 查询天赋加点
- `/tm <内容>` - 与AI对话
- `/send <频道ID> <内容>` - 发送消息到指定频道
- `/dm <用户ID> <内容>` - 发送私信给指定用户

## 依赖项目

- khl.py：开黑啦 Python SDK
- aiohttp：异步HTTP客户端/服务器
- requests：HTTP库
- python-dotenv：环境变量管理

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

本项目采用 MIT 许可证。

## 开发指南

### Git 工作流

1. 首次设置：
```bash
# 初始化本地仓库
git init

# 添加远程仓库
git remote add origin https://github.com/你的用户名/TaimeiBot.git

# 创建并切换到开发分支
git checkout -b develop
```

2. 日常开发流程：
```bash
# 获取最新代码
git pull origin develop

# 添加修改的文件
git add .

# 提交修改
git commit -m "描述你的修改"

# 推送到远程仓库
git push origin develop
```

3. 发布新版本：
```bash
# 切换到主分支
git checkout main

# 合并开发分支
git merge develop

# 创建版本标签
git tag -a v1.5.x -m "版本描述"

# 推送到远程仓库
git push origin main --tags
```

### 配置文件说明

- 所有敏感配置信息（如 token、API密钥等）都存放在 `config/config.json` 中
- 首次设置时，复制 `config/config.example.json` 为 `config/config.json` 并填入实际配置
- `config.json` 已添加到 `.gitignore`，不会被提交到版本库
