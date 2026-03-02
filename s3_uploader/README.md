# Claude Code S3 Uploader

Claude Codeの会話履歴をS3にアップロードするためのツール一式

## 📁 ファイル構成

```
.claude/
├── astemo_utils/
│   ├── enhanced_uploader.py          # Git統合機能付きアップローダー（推奨）
│   ├── claude_history_uploader.py    # シンプルアップローダー
│   ├── test_commit_filter.py         # コミットフィルターのテスト
│   └── test_git_integration.py       # Git統合のテスト
├── commands/
│   ├── upload-logs.md                # 増分アップロードコマンド
│   └── upload-logs-latest.md         # 全履歴アップロードコマンド
├── uploader_config.json.example      # 設定ファイルのサンプル
└── settings.local.json.example       # Hook設定のサンプル
```

## 🚀 セットアップ手順

### 1. 依存関係のインストール
```bash
pip install boto3
```

### 2. ファイルを任意のプロジェクトにコピー
プロジェクトのルートディレクトリに `.claude/` フォルダ全体をコピー

### 3. 設定ファイルの作成
```bash
cp .claude/uploader_config.json.example .claude/uploader_config.json
```

### 4. 設定ファイルを編集
`.claude/uploader_config.json` を編集：
```json
{
  "s3": {
    "bucket": "your-s3-bucket-name",
    "prefix": "your-prefix"
  },
  "project": {
    "name": "-home-ubuntu-your-project-name",
    "repo_path": "/path/to/your/project"
  }
}
```

### 5. （オプション）Hook設定
会話終了時の自動メッセージを設定：
```bash
cp .claude/settings.local.json.example .claude/settings.local.json
```

## 📖 使用方法

### Claude Codeコマンド

**初回アップロード（全履歴）:**
```
/upload-logs-latest
```

**2回目以降（増分アップロード）:**
```
/upload-logs
```

### コマンドライン直接実行

**全履歴アップロード:**
```bash
python3 .claude/astemo_utils/enhanced_uploader.py --mode=latest
```

**増分アップロード:**
```bash
python3 .claude/astemo_utils/enhanced_uploader.py --mode=incremental
```

**手動指定:**
```bash
python3 .claude/astemo_utils/enhanced_uploader.py \
  --mode=manual \
  --before-commit=<start-commit> \
  --after-commit=<end-commit>
```

## ⚙️ 設定オプション

### S3パス構造
```
s3://<bucket>/<prefix>/<project-name>/<commit-id>/<conversation-id>_<timestamp>.json
```

### アップロードモード
- `latest`: 初回コミットからHEADまで全てアップロード
- `incremental`: 前回アップロードからHEADまで増分アップロード
- `manual`: 手動でコミット範囲を指定

## 🧪 テスト

```bash
python3 .claude/astemo_utils/test_commit_filter.py
python3 .claude/astemo_utils/test_git_integration.py
```

## 📋 必要な環境

- Python 3.6+
- boto3 (AWS S3アクセス用)
- Git (リポジトリの場合)
- AWS認証情報の設定

## 🔧 トラブルシューティング

### よくあるエラー

1. **boto3がない**: `pip install boto3`
2. **設定ファイルがない**: `.claude/uploader_config.json`を作成
3. **AWS認証エラー**: `aws configure`でAWS認証情報を設定
4. **プロジェクト名が正しくない**: 設定ファイルの`project.name`を確認

### デバッグモード
```bash
python3 .claude/astemo_utils/enhanced_uploader.py --dry-run --mode=latest
```