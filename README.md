# Trancy 🤖

<p align="center">
  <a href="README.md">English</a> •
  <a href="README.zh.md">中文</a> •
  <a href="README.ja.md">日本語</a>
</p>

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

> A powerful Telegram bot for translation and language learning with multi-language support.

## ✨ Features

- 🌐 **Multi-language Translation** - Translate between dozens of languages
- 📚 **Language Learning** - Vocabulary building and study tools
- 🔍 **Search Functionality** - Quick search capabilities
- ⚡ **Fast & Efficient** - Built with Pyrogram for optimal performance
- 🎯 **User-friendly** - Intuitive command interface

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Telegram API credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/KaguyaTaketori/trancy.git
cd trancy

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy the example configuration:

```bash
cp .env.example .env
cp config.json.example config.json
```

2. Edit `.env` and add your Telegram API credentials:

```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
```

3. Configure `config.json` as needed.

### Usage

```bash
python bot.py
```

## 📁 Project Structure

```
trancy/
├── bot.py              # Main entry point
├── src/
│   ├── clients.py      # Telegram client setup
│   ├── config.py       # Configuration management
│   ├── handlers.py     # Message handlers
│   ├── language.py     # Language utilities
│   ├── search.py       # Search functionality
│   ├── translation.py  # Translation engine
│   └── utils.py        # Utility functions
├── LICENSE             # GPLv3 License
└── README.md           # This file
```

## 🛠️ Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show help message |
| `/lang` | Change language |
| `/translate` | Translate text |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## � License

This project is licensed under the **GNU General Public License v3.0**.

See [LICENSE](LICENSE) for more information.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/KaguyaTaketori">KaguyaTaketori</a>
</p>
