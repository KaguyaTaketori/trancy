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

> 強力な Telegram 翻訳・言語学習ボット（多言語対応）

## ✨ 機能

- 🌐 **多言語翻訳** - 数十の言語間翻訳
- 📚 **言語学習** - 語彙構築と学習ツール
- 🔍 **検索機能** - クイック検索
- ⚡ **高速・効率的** - Pyrogram で構築、最良のパフォーマンス
- 🎯 **ユーザーフレンドリー** - 直感的なコマンドインターフェース

## 🚀 クイックスタート

### 前提条件

- Python 3.10+
- Telegram API 認証情報

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/KaguyaTaketori/trancy.git
cd trancy

# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 依存関係をインストール
pip install -r requirements.txt
```

### 設定

1. 設定例をコピー：

```bash
cp .env.example .env
cp config.json.example config.json
```

2. `.env` を編集して Telegram API 認証情報を追加：

```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
```

3. 必要に応じて `config.json` を設定。

### 実行

```bash
python bot.py
```

## 📁 プロジェクト構造

```
trancy/
├── bot.py              # メインエントリポイント
├── src/
│   ├── clients.py      # Telegram クライアント設定
│   ├── config.py       # 設定管理
│   ├── handlers.py     # メッセージハンドラー
│   ├── language.py     # 言語ユーティリティ
│   ├── search.py       # 検索機能
│   ├── translation.py  # 翻訳エンジン
│   └── utils.py        # ユーティリティ関数
├── LICENSE             # GPLv3 ライセンス
└── README.md           # このファイル
```

## 🛠️ 利用可能なコマンド

| コマンド | 説明 |
|---------|------|
| `/start` | ボットを開始 |
| `/help` | ヘルプを表示 |
| `/lang` | 言語を変更 |
| `/translate` | テキストを翻訳 |

## 🤝 コントリビューション

コントリビューション大歓迎！是非 Pull Request を提交してください。

1. リポジトリを Fork
2. フィーチャーブランチを作成 (`git checkout -b feature/新機能`)
3. 変更をコミット (`git commit -m '新機能を追加'`)
4. ブランチにプッシュ (`git push origin feature/新機能`)
5. Pull Request を開く

## �ライセンス

このプロジェクトは **GNU General Public License v3.0** でライセンスされています。

詳細は [LICENSE](LICENSE) ファイルを参照してください。

---

<p align="center">
  ❤️ で開発 <a href="https://github.com/KaguyaTaketori">KaguyaTaketori</a>
</p>
