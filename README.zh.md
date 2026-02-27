# Trancy 🤖

<p align="center">
  <a href="https://github.com/KaguyaTaketori/trancy">
    <img src="https://img.shields.io/github/stars/KaguyaTaketori/trancy?style=flat-square&logo=github" alt="Stars">
  </a>
  <a href="https://github.com/KaguyaTaketori/trancy">
    <img src="https://img.shields.io/github/forks/KaguyaTaketori/trancy?style=flat-square&logo=github" alt="Forks">
  </a>
  <a href="https://github.com/KaguyaTaketori/trancy/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/KaguyaTaketori/trancy?style=flat-square" alt="License">
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+--blue?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Telegram-Bot-blue?style=flat-square&logo=telegram" alt="Telegram">
</p>

> 一个强大的 Telegram 翻译和语言学习机器人，支持多语言。

## ✨ 功能特性

- 🌐 **多语言翻译** - 支持数十种语言互译
- 📚 **语言学习** - 词汇构建和学习工具
- 🔍 **搜索功能** - 快速搜索能力
- ⚡ **快速高效** - 基于 Pyrogram 构建，性能卓越
- 🎯 **用户友好** - 直观的命令界面

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Telegram API 凭证

### 安装

```bash
# 克隆仓库
git clone https://github.com/KaguyaTaketori/trancy.git
cd trancy

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置

1. 复制配置示例：

```bash
cp .env.example .env
cp config.json.example config.json
```

2. 编辑 `.env` 并添加您的 Telegram API 凭证：

```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
```

3. 根据需要配置 `config.json`。

### 运行

```bash
python bot.py
```

## 📁 项目结构

```
trancy/
├── bot.py              # 主入口
├── src/
│   ├── clients.py      # Telegram 客户端设置
│   ├── config.py       # 配置管理
│   ├── handlers.py     # 消息处理器
│   ├── language.py     # 语言工具
│   ├── search.py       # 搜索功能
│   ├── translation.py  # 翻译引擎
│   └── utils.py        # 工具函数
├── LICENSE             # GPLv3 许可证
└── README.md           # 本文件
```

## 🛠️ 可用命令

| 命令 | 描述 |
|------|------|
| `/start` | 启动机器人 |
| `/help` | 显示帮助信息 |
| `/lang` | 更改语言 |
| `/translate` | 翻译文本 |

## 🤝 贡献

欢迎贡献代码！请随时提交 Pull Request。

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/新功能`)
3. 提交更改 (`git commit -m '添加新功能'`)
4. 推送到分支 (`git push origin feature/新功能`)
5. 打开 Pull Request

## �许可证

本项目基于 **GNU 通用公共许可证 v3.0** 授权。

详情请参阅 [LICENSE](LICENSE) 文件。

---

<p align="center">
  由 ❤️ 开发 <a href="https://github.com/KaguyaTaketori">KaguyaTaketori</a>
</p>
