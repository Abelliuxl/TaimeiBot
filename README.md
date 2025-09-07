<div align="center">
  <h1>🤖 TaimeiBot Pro</h1>
  <p><strong>专业版开黑啦机器人 | Professional Kook Bot</strong></p>
  
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Kook](https://img.shields.io/badge/Kook-Bot-orange.svg)](https://www.kookapp.cn/)
  [![WoW](https://img.shields.io/badge/WoW-Addon-red.svg)](https://worldofwarcraft.com/)
  
  <p>基于 khl.py 开发的专业开黑啦机器人，专注于魔兽世界游戏相关功能</p>
  <p>A professional Kook bot based on khl.py, focused on World of Warcraft gaming features</p>
</div>

---

## 🌟 功能特性 | Features

### 🎮 天赋查询 | Talent Query `/tf`
- 支持查询指定职业专精的天赋加点
- 从 raider.io 获取高分玩家的天赋数据
- 支持中英文职业名称和简写
- Support for querying talent builds for specific class specializations
- Talent data from high-scoring players on raider.io
- Support for both Chinese and English class names and abbreviations

**示例 | Examples:**
```
/tf 惩戒骑
/tf ret
```

### 🤖 AI对话 | AI Chat `/tm`
- 基于 DeepSeek Chat 的AI对话功能
- 模拟暴躁、专业的魔兽世界玩家风格
- AI conversation powered by DeepSeek Chat
- Simulates grumpy yet professional WoW player personality

**示例 | Examples:**
```
/tm 请问术士和法师哪个比较厉害？
/tm Which is better, Warlock or Mage?
```

### 🌐 自动翻译 | Auto Translation
- 在指定频道自动翻译中英文消息
- 支持中文转英文和英文转中文
- Automatic translation of Chinese/English messages in designated channels
- Support for Chinese to English and English to Chinese translation

### 📨 消息管理 | Message Management
- `/send` 发送消息到指定频道 | Send messages to specific channels
- `/dm` 发送私信给指定用户 | Send direct messages to users
- 支持@机器人进行对话 | Support for @bot conversations

### 🎵 语音功能 | Voice Features
- 支持加入语音频道 | Support for joining voice channels
- 音频文件播放 | Audio file playback
- FFmpeg音频转码 | FFmpeg audio transcoding

### ⚡ 专业进程管理系统 | Professional Process Management (v1.5+)
- 基于supervisord的进程管理，确保7x24小时稳定运行
- 通用supervisord命令别名系统，可管理任何服务
- 自动重启机制，崩溃后自动恢复
- 完善的日志管理和监控工具
- 简化的运维命令，大幅提升管理效率
- Process management based on supervisord for 24/7 stable operation
- Universal supervisord command alias system for managing any service
- Automatic restart mechanism for crash recovery
- Comprehensive logging and monitoring tools
- Simplified operational commands for improved efficiency

## 🚀 快速开始 | Quick Start

### 📋 环境要求 | Requirements
- Python 3.8+
- FFmpeg (用于语音功能 | For voice features)
- Supervisor (用于进程管理 | For process management)

### 🔧 安装 | Installation

1. **克隆项目 | Clone the repository:**
```bash
git clone https://github.com/Abelliuxl/TaimeiBot.git
cd TaimeiBot
```

2. **安装依赖 | Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **配置文件设置 | Configuration setup:**

创建配置文件 | Create config file:
```bash
cp config/config.example.json config/config.json
```

编辑配置文件 | Edit config file:
```json
{
    "bot_token": "your_khl_bot_token_here",
    "verify_token": "your_webhook_verify_token_here",
    "encrypt_key": "your_data_encryption_key_here",
    "llm_api_url": "https://api.openai.com/v1/chat/completions",
    "llm_api_key": "your_openai_api_key_here",
    "llm_model": "gpt-4",
    "bot_id": "726976194",
    "translation_channels": ["channel_id_1", "channel_id_2"],
    "webhook_port": 50000,
    "using_ws": true,
    "enable_translation": true,
    "enable_talent_query": true,
    "enable_ai_chat": true,
    "enable_random_reply": true
}
```

4. **配置额外文件 | Configure additional files:**

确保配置文件完整 | Ensure config files are complete:
- `config/Abbreviations.json` - 职业专精别名配置 | Class spec aliases
- `config/en_cn_wow.json` - 魔兽世界中英文翻译 | WoW term translations
- `config/member_id.txt` - 成员ID配置 | Member ID configuration

### 🏃‍♂️ 运行方式 | Running Methods

#### 方式一：直接启动 | Direct Start
```bash
python main.py
```

#### 方式二：使用进程管理系统 | Using Process Management (Recommended)

1. **加载管理命令 | Load management commands:**
```bash
source supervisor_aliases.sh
```

2. **启动supervisord | Start supervisord:**
```bash
supdaemon_start
```

3. **管理机器人 | Manage the bot:**
```bash
sup_status taimeibot        # 查看状态 | Check status
sup_start taimeibot         # 启动机器人 | Start bot
sup_restart taimeibot       # 重启机器人 | Restart bot
sup_logf taimeibot          # 实时查看日志 | View real-time logs
sup_debug taimeibot         # 调试信息 | Debug info
```

4. **批量操作 | Batch operations:**
```bash
sup_all                    # 查看所有服务状态 | Check all services
sup_restart_all            # 重启所有服务 | Restart all services
```

## 🎯 机器人命令 | Bot Commands

| 命令 | 描述 | Description |
|------|------|-------------|
| `/help` | 显示帮助信息 | Display help information |
| `/ping` | 测试机器人是否在线 | Test if bot is online |
| `/tf <职业专精>` | 查询天赋加点 | Query talent builds |
| `/tm <内容>` | 与AI对话 | Chat with AI |
| `/send <频道ID> <内容>` | 发送消息到指定频道 | Send message to channel |
| `/dm <用户ID> <内容>` | 发送私信给指定用户 | Send DM to user |

## 📁 项目结构 | Project Structure

```
TaimeiBot/
├── config/                 # 配置文件目录 | Configuration files
│   ├── Abbreviations.json # 职业专精别名配置 | Class spec aliases
│   ├── config.json        # 主配置文件 | Main config
│   ├── en_cn_wow.json    # 游戏术语翻译 | Game term translations
│   └── member.py         # 成员配置 | Member config
├── handlers/              # 消息处理模块 | Message handlers
│   ├── bot_handlers.py   # 机器人处理器 | Bot handlers
│   ├── event_handlers.py # 事件处理器 | Event handlers
│   └── message_handlers.py # 消息处理器 | Message handlers
├── services/             # 服务模块 | Service modules
│   ├── llm_service.py    # AI服务 | AI service
│   ├── message_service.py # 消息服务 | Message service
│   └── raider_service.py # Raider服务 | Raider service
├── utils/                # 工具模块 | Utility modules
│   ├── logging_utils.py  # 日志工具 | Logging utilities
│   ├── voice_utils.py    # 语音工具 | Voice utilities
│   └── error_handler.py  # 错误处理 | Error handling
├── audio/                # 音频文件 | Audio files
├── models/               # 数据模型 | Data models
├── logs/                 # 日志文件 | Log files
├── main.py              # 主程序入口 | Main entry point
└── requirements.txt     # 项目依赖 | Dependencies
```

## 🔗 依赖项目 | Dependencies

- **[khl.py](https://github.com/TWT233/khl.py)** - 开黑啦 Python SDK | Kook Python SDK
- **[aiohttp](https://docs.aiohttp.org/)** - 异步HTTP客户端/服务器 | Async HTTP client/server
- **[requests](https://requests.readthedocs.io/)** - HTTP库 | HTTP library
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** - 环境变量管理 | Environment variable management
- **[PyYAML](https://pyyaml.org/)** - YAML解析 | YAML parsing

## 🤝 贡献指南 | Contributing

欢迎提交 Issue 和 Pull Request 来帮助改进项目！
| Issues and Pull Requests are welcome to help improve the project!

### 开发指南 | Development Guide

#### Git 工作流 | Git Workflow

1. **首次设置 | Initial setup:**
```bash
# 初始化本地仓库 | Initialize local repository
git init

# 添加远程仓库 | Add remote repository
git remote add origin https://github.com/your-username/TaimeiBot.git

# 创建并切换到开发分支 | Create and switch to development branch
git checkout -b develop
```

2. **日常开发流程 | Daily development workflow:**
```bash
# 获取最新代码 | Get latest code
git pull origin develop

# 添加修改的文件 | Add modified files
git add .

# 提交修改 | Commit changes
git commit -m "描述你的修改 | Describe your changes"

# 推送到远程仓库 | Push to remote repository
git push origin develop
```

3. **发布新版本 | Release new version:**
```bash
# 切换到主分支 | Switch to main branch
git checkout main

# 合并开发分支 | Merge development branch
git merge develop

# 创建版本标签 | Create version tag
git tag -a v1.5.x -m "版本描述 | Version description"

# 推送到远程仓库 | Push to remote repository
git push origin main --tags
```

#### 配置文件说明 | Configuration Notes

- 所有敏感配置信息（如 token、API密钥等）都存放在 `config/config.json` 中
- 首次设置时，复制 `config/config.example.json` 为 `config/config.json` 并填入实际配置
- `config.json` 已添加到 `.gitignore`，不会被提交到版本库

- All sensitive configuration (tokens, API keys, etc.) is stored in `config/config.json`
- On first setup, copy `config/config.example.json` to `config/config.json` and fill in actual values
- `config.json` is added to `.gitignore` and won't be committed to version control

## 📄 许可证 | License

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 致谢 | Acknowledgments

- [khl.py](https://github.com/TWT233/khl.py) - 开黑啦 Python SDK
- [raider.io](https://raider.io/) - 提供魔兽世界数据 | For providing WoW data
- [DeepSeek](https://deepseek.com/) - AI对话支持 | AI conversation support

## 📞 联系方式 | Contact

- 提交Issue | Submit an Issue: [GitHub Issues](https://github.com/Abelliuxl/TaimeiBot/issues)
- 项目地址 | Project URL: [https://github.com/Abelliuxl/TaimeiBot](https://github.com/Abelliuxl/TaimeiBot)

---

<div align="center">
  <p><strong>⭐ 如果这个项目对你有帮助，请给个Star！| If this project helps you, please give it a star! ⭐</strong></p>
</div>
