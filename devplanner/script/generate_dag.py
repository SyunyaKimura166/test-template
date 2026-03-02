#!/usr/bin/env python3
"""
tasks.json から task-composer用 DAG JSONを生成するスクリプト

Phase 4: task-composer実行への移行で使用
改修案2: claude_code_mcp経由ではなく、直接Soda Remote MCPを呼び出す

Phase 1-C: 検証タスク自動挿入機能を追加
- タスクにvalidationフィールドがある場合、検証タスクを自動追加
- validate_output.pyを呼び出し、成果物の存在を検証

Phase 2: Ralph Loop（リトライ機構）を追加
- loop_configによるDAGレベルのループ実行
- 全検証結果を集約するvalidate_allタスク
- 前回エラー情報のプロンプトへのフィードバック
"""

import base64
import json
import os
import sys


def generate_prompt(payload: dict, enable_ralph_loop: bool = False) -> str:
    """タスク実行用のプロンプトを生成（直接呼び出し用）

    改修案2: Sodaエージェントに直接渡すプロンプト
    （Claude Code経由ではないため、シンプルな形式）

    Args:
        payload: タスク情報
        enable_ralph_loop: Ralph Loop有効時はフィードバック情報を追加
    """
    output_dir = payload.get('output_dir', '.')

    # 末尾スラッシュを正規化（パス結合の不整合を防止）
    if output_dir and output_dir != '.' and not output_dir.endswith('/'):
        output_dir = output_dir + '/'

    # 作業ディレクトリの指示を生成
    if output_dir and output_dir != '.':
        output_dir_instruction = f"""
## 重要：作業ディレクトリ（厳守）

**すべてのファイルは以下のディレクトリ配下に作成してください：**
`{output_dir}`

例：
- ソースコード: `{output_dir}src/main.py`
- テスト: `{output_dir}tests/test_main.py`
- ドキュメント: `{output_dir}docs/requirements.md`
- README: `{output_dir}README.md`

**注意**: `{output_dir}`の外側にファイルを作成しないでください。
"""
    else:
        output_dir_instruction = ""

    # Phase 2: Ralph Loopフィードバック情報
    if enable_ralph_loop:
        task_id = payload.get('task_id')
        validate_task_id = f"validate_{task_id}"
        loop_feedback = f"""
## ⚠️ リトライ情報（Ralph Loop）

**現在のイテレーション**: ${{$.loop.iteration}}
**初回実行かどうか**: ${{$.loop.first}}

### 前回の検証結果
**欠落ファイル**: ${{$.loop.previous.{validate_task_id}.output.parsed.missing_files}}
**エラー詳細**: ${{$.loop.previous.{validate_task_id}.output.parsed.errors}}

### ⚠️ 成果物作成ルール（必須・厳守）

前回の検証で欠落が検出されました。以下のルールを**必ず遵守**してください。

| ルール | 説明 |
|--------|------|
| **新規作成必須** | 欠落ファイルは**必ず新規ファイルとして作成** |
| **統合不可** | 既存ファイルへの機能追加・統合は**禁止** |
| **パス厳守** | 指定されたパスに**正確に**ファイルを作成（別パスへの作成は不可） |
| **独立性** | 類似機能が既に存在しても、**指定パスに独立ファイル**として作成 |

**具体例（禁止事項）**:
- ❌ `app/routers/auth.py`を`app/utils/auth.py`に作成 → パス違反
- ❌ `app/routers/profile.py`の機能を`app/routers/users.py`に統合 → 統合違反
- ❌ 「既に類似機能があるため作成不要」と判断してスキップ → スキップ違反

**正しい対応**:
- ✅ 欠落ファイルを**指定されたパスに必ず新規作成**
- ✅ 既存ファイルとの重複があっても**独立したファイルとして作成**

**重要**: 上記の欠落ファイルを**必ず作成**してください。
作成しない場合、再度検証エラーとなりリトライが繰り返されます。
"""
    else:
        loop_feedback = ""

    # 直接呼び出し用プロンプト（Sodaエージェントに直接渡す）
    return f"""## タスク情報
- タスクID: {payload.get('task_id')}
- タスク種別: {payload.get('task_type')}
- サブエージェント: {payload.get('agent_role')}
{output_dir_instruction}
## 実行するタスク
{payload.get('task_description')}

## 重要な注意事項
- すべてのファイルは指定されたディレクトリ配下に作成すること
- git操作は行わないでください（コミット・プッシュはシステムが自動で行います）
{loop_feedback}"""


def create_validation_task(original_task_id: str, validation: dict, output_dir: str) -> dict:
    """検証タスクを生成する

    Args:
        original_task_id: 元タスクのID
        validation: validationフィールド（expected_files, expected_directories）
        output_dir: 成果物の出力ディレクトリ

    Returns:
        検証タスクのdict
    """
    expected_files = validation.get('expected_files', [])
    expected_dirs = validation.get('expected_directories', [])

    # JSON形式でエスケープ（シェルコマンド用）
    expected_files_json = json.dumps(expected_files, ensure_ascii=False)
    expected_dirs_json = json.dumps(expected_dirs, ensure_ascii=False)

    # output_dirの正規化
    # GITHUB_WORKSPACE: GitHub Actionsで標準的に設定される作業ディレクトリ
    if output_dir and output_dir != '.':
        output_dir_arg = f"--output-dir ${{GITHUB_WORKSPACE}}/{output_dir}"
    else:
        output_dir_arg = "--output-dir ${GITHUB_WORKSPACE}"

    # validate_output.pyを呼び出すコマンド
    # シングルクォートでJSON文字列を囲む
    validate_command = (
        f"python3 ${{SCRIPT_DIR}}/validate_output.py "
        f"--expected-files '{expected_files_json}' "
        f"--expected-dirs '{expected_dirs_json}' "
        f"{output_dir_arg}"
    )

    return {
        "task_id": f"validate_{original_task_id}",
        "name": f"成果物検証: {original_task_id}",
        "executor": "bash",
        "args": {
            "command": validate_command,
            "timeout_secs": 60  # 検証は短時間で完了
        },
        "dependencies": [original_task_id]
    }


def create_validate_all_task(validation_task_ids: list) -> dict:
    """全検証結果を集約するタスクを生成する

    Args:
        validation_task_ids: 検証タスクIDのリスト

    Returns:
        validate_allタスクのdict
    """
    if validation_task_ids:
        # 検証タスクがある場合：aggregate_validation.pyで集約
        # task-composerの変数参照（${$.task_id.output.parsed}）でJSON結果を取得
        # Pythonスクリプトを使用することでJSON構築の堅牢性を確保

        # 各検証タスクの結果をJSON形式で構築
        results_parts = []
        for task_id in validation_task_ids:
            # task-composerの変数参照を使用
            # ${$.task_id.output.parsed} で検証結果全体を取得
            results_parts.append(f'"{task_id}": ${{$.{task_id}.output.parsed}}')

        results_json = "{" + ", ".join(results_parts) + "}"

        # aggregate_validation.pyを呼び出すコマンド
        # シングルクォートで囲むことでシェル展開を防止
        aggregate_command = (
            f"python3 ${{SCRIPT_DIR}}/aggregate_validation.py "
            f"--results '{results_json}'"
        )
    else:
        # 検証タスクがない場合：常に成功のJSONを出力
        aggregate_command = 'echo \'{"completed": true, "total_tasks": 0, "passed_tasks": 0, "failed_tasks": 0, "task_results": {}, "all_errors": [], "message": "検証対象なし"}\''

    return {
        "task_id": "validate_all",
        "name": "全検証結果の集約",
        "executor": "bash",
        "args": {
            "command": aggregate_command,
            "timeout_secs": 60
        },
        "dependencies": validation_task_ids
    }


def generate_dag():
    """tasks.jsonからtask-composer用DAG JSONを生成"""
    # tasks.jsonを読み込み
    try:
        with open('tasks.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: tasks.json not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: JSON parse failed: {e}")
        sys.exit(1)

    if 'tasks' not in data or not isinstance(data['tasks'], list):
        print("Error: Invalid tasks.json structure - 'tasks' array required")
        sys.exit(1)

    dag_tasks = []
    validation_task_ids = []  # Phase 2: 検証タスクIDを追跡

    # Ralph Loop設定（環境変数で制御可能）
    enable_ralph_loop = os.environ.get('ENABLE_RALPH_LOOP', 'false').lower() == 'true'
    max_iterations = int(os.environ.get('RALPH_LOOP_MAX_ITERATIONS', '3'))

    for task in data.get('tasks', []):
        payload = task.get('payload', {})
        role = task.get('role', {})

        # デフォルトのrole設定
        if not role:
            role = {
                "role_id": "default_role",
                "name": "Default Role",
                "file_permissions": {
                    "allowed_paths": [],
                    "read_only_paths": [],
                    "denied_paths": [".env", "secrets/"]
                }
            }

        # task-composerが必要とするroleフィールドを追加
        # 参照: 動作確認手順書.md セクション5.1
        role_for_dag = {
            "role_id": role.get("role_id", "default_role"),
            "name": role.get("name", "Default Role"),
            "subagents": role.get("subagents", []),
            "skills": role.get("skills", []),
            "description": role.get("description", ""),
            "tool_permissions": role.get("tool_permissions", {
                "bash": {
                    "allowed_commands": [],
                    "blocked_commands": [],
                    "require_confirmation": []
                },
                "write": {
                    "max_file_size_mb": None,
                    "allowed_extensions": []
                }
            }),
            "file_permissions": role.get("file_permissions", {
                "allowed_paths": [],
                "read_only_paths": [],
                "denied_paths": [".env", "secrets/"]
            })
        }

        # 改修案2: bash executor + soda_invoker.py で直接呼び出し
        #
        # 必要な環境変数（ワークフロー側で設定が必要）:
        #   - SCRIPT_DIR: このスクリプトが配置されているディレクトリ
        #   - SODA_MCP_RUNTIME_ID: Soda Remote MCPのランタイムID
        #   - SODA_MCP_QUALIFIER: エージェントのqualifier（例: DEFAULT）
        #   - COGNITO_*: Cognito認証情報
        #
        # soda_invoker.pyに渡すパラメータをJSON形式で構築
        soda_params = {
            "prompt": generate_prompt(payload, enable_ralph_loop),
            "repo_url": payload.get('repo_url'),
            "branch": payload.get('base_branch'),
            "subagent": payload.get('agent_role'),
            "auto_commit": True,
            "auto_push": True,
            "include_history": False
        }

        # output_dirが指定されている場合のみfile_permissionsを追加
        output_dir = payload.get('output_dir')
        if output_dir and output_dir != '.':
            soda_params["file_permissions"] = {
                "allowed_paths": [
                    f"${{project_root}}/{output_dir}",
                    f"${{project_root}}/{output_dir}/**"
                ]
            }

        # JSONをBase64エンコードしてシェルの特殊文字問題を回避
        # （改行、クォート、バックスラッシュ等の安全なエスケープ）
        soda_params_json = json.dumps(soda_params, ensure_ascii=False)
        soda_params_b64 = base64.b64encode(soda_params_json.encode('utf-8')).decode('ascii')

        dag_task = {
            "task_id": payload.get('task_id'),
            "name": payload.get('task_description', payload.get('task_id', 'Unknown Task')),
            "executor": "bash",
            "args": {
                # BashExecutorはargs.commandを単一のシェルコマンドとして実行
                # args.argsは無視されるため、全コマンドをcommandに含める
                # Base64エンコードによりシェルの特殊文字問題を回避
                "command": "python3 ${SCRIPT_DIR}/soda_invoker.py --base64 " + soda_params_b64,
                # NOTE: 以下のenv設定は現在BashExecutorに無視される（ctx.env_varsのみ参照）
                # 対応案Aによりワークフローのプロセス環境変数から継承するため、
                # 実際にはこの設定は使用されない。
                # 将来のtask-composer修正（対応案B/C）に備えて残している。
                "env": {
                    # Soda Remote MCP設定
                    "SODA_MCP_REGION": "${SODA_MCP_REGION}",
                    "SODA_MCP_RUNTIME_ID": "${SODA_MCP_RUNTIME_ID}",
                    "SODA_MCP_QUALIFIER": "${SODA_MCP_QUALIFIER}",
                    # Cognito認証設定
                    "COGNITO_USER_POOL_ID": "${COGNITO_USER_POOL_ID}",
                    "COGNITO_CLIENT_ID": "${COGNITO_CLIENT_ID}",
                    "COGNITO_USERNAME": "${COGNITO_USERNAME}",
                    "COGNITO_PASSWORD": "${COGNITO_PASSWORD}",
                    # AWS認証情報（OIDC認証で取得した一時認証情報）
                    "AWS_REGION": "${AWS_REGION}",
                    "AWS_ACCESS_KEY_ID": "${AWS_ACCESS_KEY_ID}",
                    "AWS_SECRET_ACCESS_KEY": "${AWS_SECRET_ACCESS_KEY}",
                    "AWS_SESSION_TOKEN": "${AWS_SESSION_TOKEN}",
                    # タイムアウト設定（envsubstは:-構文未対応のため単純形式）
                    "SODA_CONNECT_TIMEOUT": "${SODA_CONNECT_TIMEOUT}",
                    "SODA_READ_TIMEOUT": "${SODA_READ_TIMEOUT}"
                },
                "cwd": payload.get('output_dir', '.'),
                # BashExecutorのタイムアウト設定（デフォルト300秒では不足）
                # Soda Remote MCPの処理時間を考慮して1800秒（30分）に設定
                "timeout_secs": 1800
            },
            "role": role_for_dag,
            "dependencies": task.get('dependencies', [])
        }

        dag_tasks.append(dag_task)

        # Phase 1-C: validationフィールドがある場合、検証タスクを自動追加
        validation = task.get('validation')
        if validation and (validation.get('expected_files') or validation.get('expected_directories')):
            validation_task = create_validation_task(
                original_task_id=payload.get('task_id'),
                validation=validation,
                output_dir=payload.get('output_dir', '.')
            )
            dag_tasks.append(validation_task)
            validation_task_ids.append(validation_task['task_id'])  # Phase 2: IDを記録

    # Phase 2: Ralph Loop用のvalidate_allタスクを追加（検証タスクがある場合のみ）
    if validation_task_ids and enable_ralph_loop:
        validate_all_task = create_validate_all_task(validation_task_ids)
        dag_tasks.append(validate_all_task)

    # DAG構造を作成
    dag = {
        "tasks": dag_tasks,
        "config": {
            "max_concurrent_tasks": int(os.environ.get('MAX_CONCURRENT_TASKS', '4')),
            "default_task_timeout_secs": int(os.environ.get('DEFAULT_TASK_TIMEOUT_SECS', '1800'))
        }
    }

    # Phase 2: Ralph Loop設定を追加（有効な場合のみ）
    if enable_ralph_loop and validation_task_ids:
        dag["loop_config"] = {
            "max_iterations": max_iterations,
            "until_condition": "$.validate_all.output.parsed.completed == true"
        }

    # 出力ファイル名（環境変数で変更可能）
    output_file = os.environ.get('DAG_OUTPUT_FILE', 'dag_for_execution.json')

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dag, f, indent=2, ensure_ascii=False)

    # 統計情報を計算
    validation_task_count = sum(1 for t in dag_tasks if t['task_id'].startswith('validate_'))
    aggregate_task_count = 1 if (enable_ralph_loop and validation_task_ids) else 0
    original_task_count = len(dag_tasks) - validation_task_count - aggregate_task_count

    print(f"✅ DAG JSON生成完了: {output_file}")
    print(f"   タスク数: {len(dag_tasks)} (実行: {original_task_count}, 検証: {validation_task_count}, 集約: {aggregate_task_count})")

    # Phase 2: Ralph Loop情報を表示
    if enable_ralph_loop and validation_task_ids:
        print(f"   🔄 Ralph Loop: 有効 (最大{max_iterations}回)")
    elif enable_ralph_loop:
        print(f"   🔄 Ralph Loop: 有効だが検証タスクなし（ループ無効）")
    else:
        print(f"   🔄 Ralph Loop: 無効 (ENABLE_RALPH_LOOP=true で有効化)")

    # タスク一覧を表示
    for task in dag_tasks:
        deps = task.get('dependencies', [])
        deps_str = f" (依存: {', '.join(deps)})" if deps else ""
        task_name = task['name']
        task_name_display = f"{task_name[:50]}..." if len(task_name) > 50 else task_name
        print(f"   - {task['task_id']}: {task_name_display}{deps_str}")


if __name__ == "__main__":
    generate_dag()
