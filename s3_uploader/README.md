# Claude Code Agents Template

このリポジトリは、Claude Codeのカスタムエージェントを使用したGitHub Actionsワークフローのテンプレートを提供します。

## 概要

このテンプレートを使用すると、GitHubのissueやPRコメントでエージェントをメンションするだけで、AI駆動のカスタムエージェントが自動的に起動し、様々なタスクを実行できます。

さらに、Claude Codeとの会話履歴を自動的にAWS S3にアップロードする機能を備えており、開発プロセスの記録と分析を容易にします。

### 提供されるエージェント例

このテンプレートには、以下のエージェント例が含まれています：

#### 1. バグ分析エージェント (`@bug-analysis-claude`)

GitHubのissueやPRコメントで `@bug-analysis-claude` をメンションすると、包括的なバグ分析を実行します。

- ルート原因分析
- 影響評価と修正提案
- 視覚化サポート（アプリケーションサイクルグラフ、タイミングチャート等）
- ブランチ指定対応（`@@<branch-name>` 形式）

## 主な機能

- **カスタムエージェント**: 目的に応じた専用エージェントを定義可能
- **GitHub Actions統合**: issueやPRコメントでエージェントをトリガー
- **ブランチ指定**: `@@<branch-name>` 形式で作業ブランチを指定可能
- **AWS Bedrock統合**: Claude Sonnet 4.5モデルを使用した高度なAI機能
- **柔軟なカスタマイズ**: エージェントの動作、使用可能なツール、モデル設定などを自由にカスタマイズ
- **ログアップロード**: Claude Code会話履歴をS3にアップロード、Git統合による詳細なメタデータ付き

## セットアップ

### 必要な要件

- GitHub App（リポジトリへのアクセス権限）
- AWS IAMロール（Bedrock APIアクセス用）
- GitHub Secrets の設定

### GitHub Secrets の設定

以下のシークレットをリポジトリに追加してください：

```
APP_ID: GitHub AppのID
APP_PRIVATE_KEY: GitHub Appのプライベートキー
AWS_ROLE_TO_ASSUME: AWS BedrockアクセスのためのIAMロールARN
```

### ワークフローの配置

1. `.github/workflows/` ディレクトリに `claude-code-bug-analysis-actions.yaml` をコピー
2. 必要に応じてワークフロー設定をカスタマイズ

## 使用方法

### 基本的な使用

issueまたはPRコメントでエージェントをメンションします。

**例: バグ分析エージェント**

```
@bug-analysis-claude
ログイン機能でNullPointerExceptionが発生しています。
原因を調査してください。
```

### ブランチ指定

特定のブランチを指定してエージェントを実行する場合：

```
@bug-analysis-claude @@feature/new-api
この機能でパフォーマンス問題が発生しています。
```

ブランチ名のフォーマット：
- `@@feature/feature-name`
- `@@bugfix/bug-description`
- `@@release/v1.2.3`
- `@@hotfix/critical-fix`

## ログアップロード機能

Claude Codeとの会話履歴をAWS S3に自動アップロードする機能を提供します。コミット範囲でフィルタリングし、Git統合による詳細なメタデータを含めることができます。

### セットアップ

1. **設定ファイルを作成** (`.claude/uploader_config.json`):

サンプルファイル (`.claude/uploader_config.json.example`) をコピーして使用できます：
```bash
cp .claude/uploader_config.json.example .claude/uploader_config.json
# エディタで自分のS3バケット名を設定
```

または、以下の形式で作成：
```json
{
  "s3": {
    "bucket": "your-s3-bucket-name",
    "prefix": "commit_base"
  },
  "project": {
    "name": "-home-ubuntu-agents-templete",
    "repo_path": "/home/ubuntu/agents-templete"
  }
}
```

設定オプション：
- `s3.bucket`: S3バケット名
- `s3.prefix`: S3キープレフィックス
- `project.name`: プロジェクト名（省略可、コマンドで指定も可）
- `project.repo_path`: Gitリポジトリパス（省略可、コマンドで指定も可）

**注意**: 設定ファイルはプロジェクトディレクトリの `.claude/` 下に配置します。これにより、各プロジェクトが独自の設定を持つことができます。

2. **AWSクレデンシャルを設定**:
```bash
aws configure
```

### 使用方法

#### カスタムコマンド

**インクリメンタルアップロード** (`/upload-logs`):
- 前回のアップロードから現在のHEADまでの新しいログをアップロード
- 初回使用前に `/upload-logs-latest` を実行する必要があります

**全ログアップロード** (`/upload-logs-latest`):
- 最初のコミットから現在のHEADまでの全ログをアップロード
- アップロード履歴を保存し、以降のインクリメンタルアップロードを可能にします

どちらのコマンドも：
1. Git statusを確認し、変更ファイルを表示
2. ユーザーに確認を求める
3. コミットメッセージを入力
4. 変更をコミットしてログをアップロード

#### 手動実行

**インクリメンタルモード** (前回からの差分):
```bash
python3 .claude/astemo_utils/enhanced_uploader.py \
  --project=-home-ubuntu-agents-template \
  --repo-path=/home/ubuntu/agents-template \
  --mode=incremental
```

**Latestモード** (全履歴):
```bash
python3 .claude/astemo_utils/enhanced_uploader.py \
  --project=-home-ubuntu-agents-template \
  --repo-path=/home/ubuntu/agents-template \
  --mode=latest
```

**Manualモード** (コミット範囲を指定):
```bash
python3 .claude/astemo_utils/enhanced_uploader.py \
  --project=-home-ubuntu-agents-template \
  --repo-path=/home/ubuntu/agents-template \
  --mode=manual \
  --before-commit=<開始コミットハッシュ> \
  --after-commit=<終了コミットハッシュ>
```

### アップロードされるデータ

- **会話メッセージ**: Claude Codeとのやり取り全体
- **Gitメタデータ**: コミット情報、変更ファイル、差分統計
- **トークン使用量**: 入力/出力トークン数
- **I/Oサマリー**: 読み込み/書き込みファイル、実行コマンド
- **環境情報**: ブランチ、ユーザー、タイムスタンプ

詳細なスキーマについては [SCHEMA.md](SCHEMA.md) を参照してください。

### S3アップロード先

ファイルは以下のパスにアップロードされます：
```
s3://<bucket>/<prefix>/<project-name>/<commit-id>/<conversation-id>_<timestamp>.json
```

例：
```
s3://claude-code-history/commit_base/-home-ubuntu-agents-template/0925167c3d15b54876313ff11cf31fa24e8236d2/daddead0-622a-4cf9-9197-9d5e4aacfb60_20251021_121446.json
```

## プロジェクト構造

```
.
├── .claude/
│   ├── agents/
│   │   └── bug-analysis-agent.md     # バグ分析エージェントの定義
│   ├── astemo_utils/                 # Claude Code補助ユーティリティ
│   │   ├── claude_history_uploader.py    # 基本ログアップローダー
│   │   ├── enhanced_uploader.py          # Git統合版アップローダー
│   │   ├── test_commit_filter.py         # コミットフィルターのテスト
│   │   └── test_git_integration.py       # Git統合のテスト
│   ├── commands/
│   │   ├── upload-logs.md            # インクリメンタルアップロードコマンド
│   │   └── upload-logs-latest.md     # 全ログアップロードコマンド
│   └── uploader_config.json.example  # 設定ファイルのサンプル
├── .github/
│   └── workflows/
│       └── claude-code-bug-analysis-actions.yaml  # GitHub Actionsワークフロー
├── claude_code/
│   └── workflows/
│       ├── utils/
│       │   ├── parse_branch.py       # ブランチ名パーサー
│       │   ├── test_parse_branch.py  # パーサーのテスト
│       │   └── README.md            # ユーティリティのドキュメント
│       └── github_actions/
│           └── claude-code-bug-analysis-actions.yaml  # ワークフローテンプレート
├── CLAUDE.md                         # Claude Code向けプロジェクト指示
├── SCHEMA.md                         # ログデータスキーマ定義
└── README.md
```

## エージェントの機能例

### バグ分析エージェント

テンプレートに含まれるバグ分析エージェントは以下の分析を実行します：

1. **体系的な調査**
   - エラーメッセージ、スタックトレース、ログの収集
   - 実行フローの追跡
   - タイミング問題や競合状態の考慮

2. **ルート原因分析**
   - 表面的な症状ではなく根本原因を特定
   - 最近のコード変更のレビュー
   - 関連コンポーネントと依存関係の調査

3. **包括的レポート**
   - バグの概要
   - 再現手順
   - ルート原因の詳細説明
   - 影響評価
   - 修正提案とコード例
   - 予防戦略

4. **視覚化とタイミング分析**
   - 実行期間の可視化
   - 同期分析
   - タイミング異常の検出

## カスタムエージェントの作り方

効果的なカスタムエージェントを作成するには、以下のワークフローを推奨します：

### ステップ1: Vibeコーディングで例題を解く

まず、Claude Codeと対話しながら、エージェントに解決させたいタスクの例題を実際に解きます。

1. **具体的なタスクを選ぶ**
   - エージェントに担当させたい典型的なタスク（例: バグ分析、コードレビュー、テスト生成等）を選択

2. **Claude Codeと協働して解決**
   - Claude Codeとの自然な対話を通じて問題を解決
   - 効果的だったアプローチ、使用したツール、思考プロセスを観察
   - 複数の類似タスクで実験し、パターンを特定

3. **会話履歴と実験データを保存**
   - 成功した会話の履歴を保存
   - 使用したツール、コマンド、分析手法を記録
   - 効果的だった指示やプロンプトをメモ

**例: バグ分析エージェントの場合**
```
ユーザー: "このコードでメモリリークが発生しています。原因を調査してください。"

Claude Code:
- まずエラーログを確認
- 関連するコードファイルを読み取り
- メモリプロファイリングツールを実行
- スタックトレースを分析
- ルート原因を特定し、修正案を提示

→ この一連のアプローチと使用したツールをドキュメント化
```

### ステップ2: サブエージェント定義を作成

会話履歴と実験データを基に、専用のサブエージェントを定義します。

#### 2-1. エージェント定義ファイルの作成

`.claude/agents/` ディレクトリに新しいMarkdownファイルを作成します：

```bash
# プロジェクト固有のエージェント
.claude/agents/your-agent-name.md

# または、全プロジェクトで使用可能なエージェント
~/.claude/agents/your-agent-name.md
```

#### 2-2. YAML Frontmatterの設定

ファイルの先頭にメタデータを定義します：

```yaml
---
name: your-agent-name
description: |
  このエージェントを起動すべきタイミングと目的を自然な言語で記述。
  複数の例を含めると、Claude Codeが適切に判断できます。

  例:
  - ユーザーがバグ報告を行った時
  - エラーログの分析が必要な時
  - パフォーマンス問題の調査が必要な時

tools: Read, Write, Edit, Bash, Grep, Glob  # 使用可能なツール（省略時は全ツール）
model: sonnet  # sonnet, opus, haiku, または inherit
color: blue  # UI表示用の色
---
```

#### 2-3. システムプロンプトの作成

Vibeコーディングで得た知見を基に、エージェントの役割と動作を定義します：

```markdown
あなたは[専門分野]の専門家です。[具体的な役割と責任]を担当します。

## 主な責任

1. **[責任1]**
   - [具体的なアクション]
   - [使用する手法]

2. **[責任2]**
   - [具体的なアクション]
   - [使用する手法]

## ワークフロー

[Vibeコーディングで効果的だった手順を記述]

1. [ステップ1]: [詳細な説明]
2. [ステップ2]: [詳細な説明]
3. [ステップ3]: [詳細な説明]

## ベストプラクティス

- [観察された効果的なアプローチ]
- [避けるべきアンチパターン]
- [推奨するツールや手法]

## 出力形式

[期待される出力の形式やテンプレート]
```

#### 2-4. 実例からの抽出ポイント

Vibeコーディングで得た会話履歴から以下を抽出してプロンプトに組み込みます：

- **効果的だった質問**: どのような情報を収集したか
- **使用したツール**: どのツールをどの順序で使用したか
- **分析手法**: どのようなアプローチで問題を解決したか
- **成功パターン**: 複数のタスクで共通していた成功パターン
- **エッジケース**: 注意が必要な特殊なケース

### ステップ3: GitHub Actionsワークフローの作成

エージェントをGitHub Actionsで使用するためのワークフローを作成します：

`.github/workflows/your-agent-workflow.yaml`

```yaml
name: Your Agent Action

permissions:
  contents: write
  pull-requests: write
  issues: write
  id-token: write
  actions: write

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]

jobs:
  your-agent:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@your-agent')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@your-agent')) ||
      (github.event_name == 'issues' && contains(github.event.issue.body, '@your-agent'))
    runs-on: ubuntu-latest
    env:
      AWS_REGION: us-east-1
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Parse Base Branch
        id: parse_branch
        run: |
          if [[ "${{ github.event_name }}" == "issues" ]]; then
            INPUT_TEXT="${{ github.event.issue.body }}"
          else
            INPUT_TEXT="${{ github.event.comment.body }}"
          fi

          BRANCH_NAME=$(echo "$INPUT_TEXT" | python3 claude_code/workflows/utils/parse_branch.py 2>/dev/null || echo "")
          BASE_BRANCH="${BRANCH_NAME:-main}"

          if [[ ${#BASE_BRANCH} -gt 100 ]]; then
            echo "Branch name too long, using default: main"
            BASE_BRANCH="main"
          fi

          echo "base_branch=$BASE_BRANCH" >> $GITHUB_OUTPUT

      - name: Generate GitHub App token
        id: app-token
        uses: actions/create-github-app-token@v2
        with:
          app-id: ${{ secrets.APP_ID }}
          private-key: ${{ secrets.APP_PRIVATE_KEY }}

      - name: Configure AWS Credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_TO_ASSUME }}
          aws-region: us-east-1

      - uses: anthropics/claude-code-action@v1
        with:
          trigger_phrase: "@your-agent"
          base_branch: ${{ steps.parse_branch.outputs.base_branch }}
          github_token: ${{ steps.app-token.outputs.token }}
          use_bedrock: "true"
          claude_args: |
            --system-prompt "Use @your-agent-name. [追加の指示をここに記述]"
            --max-turns 10000
            --model "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
            --allowed-tools "git fetch,git pull,git merge,git push,git add,git commit,git status,git diff,Bash,WebFetch,Task,Read,Write,Edit,Glob,Grep,TodoWrite"
```

### ステップ4: テストと改善

1. **初期テスト**
   - 実際のissueやPRでエージェントをトリガー
   - Vibeコーディングで解決した同じタイプの問題を試す

2. **動作の観察**
   - エージェントの出力を確認
   - 期待通りのツールを使用しているか
   - 分析手法が適切か

3. **継続的改善**
   - 不足している指示をプロンプトに追加
   - 新しいパターンやベストプラクティスを発見したら更新
   - エッジケースへの対応を追加

### エージェント作成のベストプラクティス

- **具体的な例を含める**: description に具体的な使用例を記載
- **明確な責任範囲**: エージェントの役割を明確に定義し、範囲を限定
- **ツールの制限**: 必要最小限のツールのみを許可してセキュリティを向上
- **段階的アプローチ**: システムプロンプトに明確なステップバイステップの手順を記載
- **出力形式の指定**: 期待される出力形式やレポート構造を明示
- **実例ベース**: Vibeコーディングで実際に成功した手法を基に作成

## カスタマイズ

### ワークフロー設定

各エージェントのワークフローファイル（例: `claude-code-bug-analysis-actions.yaml`）で以下をカスタマイズできます：

- `trigger_phrase`: エージェントを起動するフレーズ（例: `@bug-analysis-claude`）
- `max-turns`: エージェントの最大ターン数（デフォルト: 10000）
- `model`: 使用するClaudeモデル（例: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`）
- `allowed-tools`: エージェントが使用できるツールのリスト
- `system-prompt`: エージェントに指示する追加プロンプト

### エージェントのカスタマイズ

`.claude/agents/` ディレクトリ内のエージェント定義ファイルを編集して、エージェントの動作、責任、分析手法などをカスタマイズできます。

**エージェント定義ファイルの主要項目:**
- `name`: エージェント名
- `description`: エージェントの説明と使用例
- `model`: 使用するモデル（sonnet, haiku等）
- `color`: エージェントの色（UI表示用）
- プロンプト本文: エージェントの役割、責任、ワークフロー、ベストプラクティス等

## ユーティリティ

### ブランチ名パーサー

`claude_code/workflows/utils/parse_branch.py` は、テキストから `@@<branch-name>` 形式のブランチ名を抽出するユーティリティです。

詳細は [claude_code/workflows/utils/README.md](claude_code/workflows/utils/README.md) を参照してください。

## ライセンス

このテンプレートは自由に使用、変更、配布できます。

## サポート

問題が発生した場合は、issueを作成してください。