# Enhanced Log Schema Documentation

## Overview

このスキーマは、Claude Code の会話履歴を Git コミット情報と統合して管理するためのものです。

## Schema Structure

```json
{
  "session": {
    "id": "uuid-v4",
    "conversation_id": "string",
    "started_at": "ISO8601 timestamp",
    "ended_at": "ISO8601 timestamp",
    "duration_seconds": 0
  },
  "data": {
    "conversation": {
      "messages": [],
      "total_turns": 0,
      "total_tokens": {
        "input": 0,
        "output": 0,
        "total": 0
      }
    },
    "git": {
      "commits": {
        "before": "commit_hash",
        "after": "commit_hash"
      },
      "branch": {
        "name": "string",
        "base": "string"
      },
      "changes": {
        "files_added": [],
        "files_modified": [],
        "files_deleted": [],
        "total_additions": 0,
        "total_deletions": 0
      }
    },
    "io_summary": {
      "user_requests": [],
      "agent_actions": {
        "tool_uses": [],
        "files_read": [],
        "files_written": [],
        "commands_executed": []
      },
      "outcomes": {
        "completed_tasks": [],
        "failed_tasks": [],
        "errors": []
      }
    }
  },
  "metadata": {
    "project": {
      "name": "string",
      "repo_url": "string",
      "local_path": "string"
    },
    "user": {
      "id": "string (e.g. github_username)",
      "email": "string (optional)"
    },
    "agent": {
      "name": "string (e.g. claude-code)",
      "model": "string (e.g. claude-sonnet-4.5) - most used model",
      "model_usage": {
        "claude-sonnet-4-5-20250929": 35,
        "claude-3-5-haiku-20241022": 5
      },
      "version": "string"
    },
    "environment": {
      "os": "string",
      "platform": "string",
      "working_directory": "string"
    },
    "feedback": {
      "rating": "integer (1-5, optional)",
      "comment": "string (optional)",
      "submitted_at": "ISO8601 timestamp (optional)"
    }
  }
}
```

## Field Descriptions

### session

セッション全体に関する情報

- **id**: セッションの一意識別子 (UUID v4)
- **conversation_id**: Claude Code の会話ID
- **started_at**: セッション開始時刻 (ISO8601)
- **ended_at**: セッション終了時刻 (ISO8601)
- **duration_seconds**: セッション継続時間（秒）

### data.conversation

会話の内容に関する情報

- **messages**: 会話メッセージの配列（元のJSONL形式）
- **total_turns**: メッセージの総数
- **total_tokens**: トークン使用量の統計
  - **input**: 入力トークン数
  - **output**: 出力トークン数
  - **total**: 合計トークン数

### data.git

Git リポジトリの変更情報

- **commits**: コミット範囲
  - **before**: 開始コミットハッシュ
  - **after**: 終了コミットハッシュ
- **branch**: ブランチ情報
  - **name**: 現在のブランチ名
  - **base**: ベースブランチ名（オプション）
- **changes**: ファイル変更統計
  - **files_added**: 追加されたファイルのリスト
  - **files_modified**: 変更されたファイルのリスト
  - **files_deleted**: 削除されたファイルのリスト
  - **total_additions**: 追加された行数
  - **total_deletions**: 削除された行数

### data.io_summary

入出力の要約情報

- **user_requests**: ユーザーからのリクエスト一覧
- **agent_actions**: エージェントのアクション
  - **tool_uses**: 使用されたツールのリスト
  - **files_read**: 読み込まれたファイルのリスト
  - **files_written**: 書き込まれたファイルのリスト
  - **commands_executed**: 実行されたコマンドのリスト
- **outcomes**: 結果
  - **completed_tasks**: 完了したタスクのリスト
  - **failed_tasks**: 失敗したタスクのリスト
  - **errors**: エラーのリスト

### metadata

メタデータ情報

- **project**: プロジェクト情報
  - **name**: プロジェクト名
  - **repo_url**: リポジトリURL
  - **local_path**: ローカルパス
- **user**: ユーザー情報
  - **id**: ユーザーID（例: GitHubユーザー名）
  - **email**: メールアドレス（オプション）
- **agent**: エージェント情報
  - **name**: エージェント名
  - **model**: 最も使用されたモデル
  - **model_usage**: 各モデルの使用回数（例: `{"claude-sonnet-4-5": 35, "claude-3-5-haiku": 5}`）
  - **version**: エージェントのバージョン
- **environment**: 実行環境情報
  - **os**: オペレーティングシステム
  - **platform**: プラットフォーム
  - **working_directory**: 作業ディレクトリ
- **feedback**: フィードバック（オプション）
  - **rating**: 評価（1-5）
  - **comment**: コメント
  - **submitted_at**: 提出日時

## Usage Example

### 基本的な使用方法

```bash
# 全ての会話を出力
python3 enhanced_uploader.py \
  --output-dir ./output \
  --project "-home-ubuntu-myproject" \
  --repo-path /home/ubuntu/myproject

# 特定のコミット範囲の会話のみを抽出
python3 enhanced_uploader.py \
  --output-dir ./output \
  --project "-home-ubuntu-myproject" \
  --repo-path /home/ubuntu/myproject \
  --before-commit abc1234 \
  --after-commit def5678

# S3にアップロード
python3 enhanced_uploader.py \
  --bucket my-bucket \
  --prefix claude_logs \
  --project "-home-ubuntu-myproject" \
  --repo-path /home/ubuntu/myproject \
  --before-commit abc1234 \
  --after-commit def5678

# Dry run（実際にアップロード/保存せずにテスト）
python3 enhanced_uploader.py \
  --output-dir ./output \
  --project "-home-ubuntu-myproject" \
  --dry-run
```

## コミット範囲でのフィルタリング

`--before-commit` と `--after-commit` オプションを使用すると、指定されたコミット範囲内のタイムスタンプを持つ会話メッセージのみが抽出されます。

- **before-commit**: この時刻以降の会話を含む
- **after-commit**: この時刻以前の会話を含む

これにより、特定の開発セッションやスプリントに関連する会話のみを抽出できます。

## Benefits

1. **トレーサビリティ**: コードの変更と会話履歴を関連付けることで、意思決定の経緯を追跡可能
2. **コスト分析**: トークン使用量の統計により、プロジェクトのAI利用コストを分析
3. **セッション管理**: 開始/終了時刻と継続時間により、作業セッションを把握
4. **品質向上**: フィードバック機能により、エージェントの品質を継続的に改善
5. **Git統合**: コミット範囲での会話抽出により、特定の開発期間の分析が可能
