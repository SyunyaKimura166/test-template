# Branch Name Parser

テキストから `@@<ブランチ名>` 形式でブランチ名をパースするPythonユーティリティです。

## 機能

- テキストから単一のブランチ名をパース
- テキストから全てのブランチ名をパース
- ブランチマーカーを除去したテキストとブランチ名を取得
- コマンドラインツールとしても使用可能

## 使用方法

### Pythonモジュールとして使用

```python
from parse_branch import parse_branch_name, parse_all_branch_names, extract_text_and_branch

# 単一のブランチ名をパース
branch = parse_branch_name("@@feature/new-api を作成してください")
print(branch)  # "feature/new-api"

# 全てのブランチ名をパース
branches = parse_all_branch_names("@@feature/a と @@feature/b を作成")
print(branches)  # ["feature/a", "feature/b"]

# テキストとブランチ名を分離
text, branch = extract_text_and_branch("Create @@feature/api endpoint")
print(text)    # "Create  endpoint"
print(branch)  # "feature/api"
```

### コマンドラインツールとして使用

```bash
# 引数として渡す
python3 parse_branch.py "@@feature/new-api を作成してください"
# 出力: feature/new-api

# 標準入力から読み取る
echo "Create @@release/v1.2.3 branch" | python3 parse_branch.py
# 出力: release/v1.2.3
```

## サポートされるブランチ名の文字

- 英数字: `a-z`, `A-Z`, `0-9`
- ハイフン: `-`
- アンダースコア: `_`
- スラッシュ: `/`
- ドット: `.`

## ブランチ名の例

- `@@feature/new-api`
- `@@bugfix/login-error`
- `@@release/v1.2.3`
- `@@feature/user_authentication`
- `@@hotfix/critical-bug`

## テスト

ユニットテストを実行するには:

```bash
python3 test_parse_branch.py -v
```

## 終了コード

コマンドラインツールとして使用する場合:
- `0`: ブランチ名が正常にパースされた
- `1`: ブランチ名が見つからなかった、または入力が空
