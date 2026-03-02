#!/usr/bin/env python3
"""検証結果集約スクリプト

task-composerのvalidate_allタスクから呼び出され、
複数の検証タスク結果を集約してJSON形式で出力する。

Usage:
    python3 aggregate_validation.py --results '{"task1": {"completed": true}, "task2": {"completed": false, "errors": [...]}}'

Output:
    JSON形式で集約結果を標準出力に出力（task-composerのoutput.parsedで参照可能）

Examples:
    # task-composerから呼び出される形式
    python3 aggregate_validation.py --results '${JSON_RESULTS}'
"""

import argparse
import json
import sys


def aggregate_results(results: dict) -> dict:
    """複数の検証結果を集約する

    Args:
        results: 検証タスクIDをキー、検証結果をvalueとするdict
                 各valueは {"completed": bool, "errors": [...], ...} の形式

    Returns:
        集約結果のdict
    """
    output = {
        "completed": True,
        "total_tasks": len(results),
        "passed_tasks": 0,
        "failed_tasks": 0,
        "task_results": {},
        "all_errors": [],
        "message": ""
    }

    for task_id, result in results.items():
        completed = result.get("completed", False)
        errors = result.get("errors", [])

        output["task_results"][task_id] = {
            "completed": completed,
            "error_count": len(errors)
        }

        if completed:
            output["passed_tasks"] += 1
        else:
            output["completed"] = False
            output["failed_tasks"] += 1
            # エラー情報にタスクIDを付与して集約
            for error in errors:
                output["all_errors"].append(f"[{task_id}] {error}")

    # メッセージ生成
    if output["completed"]:
        output["message"] = f"全ての成果物検証に成功しました ({output['passed_tasks']}/{output['total_tasks']} タスク)"
    else:
        output["message"] = f"一部の成果物が欠落しています ({output['failed_tasks']}/{output['total_tasks']} タスクが失敗)"

    return output


def main():
    parser = argparse.ArgumentParser(description="検証結果集約スクリプト")
    parser.add_argument("--results", type=str, required=True,
                        help="検証結果のJSON（タスクID -> 結果のdict）")

    args = parser.parse_args()

    try:
        results = json.loads(args.results)
    except json.JSONDecodeError as e:
        # JSONパースエラー時も有効なJSONを出力
        print(json.dumps({
            "completed": False,
            "total_tasks": 0,
            "passed_tasks": 0,
            "failed_tasks": 0,
            "task_results": {},
            "all_errors": [f"JSON parse error: {e}"],
            "message": f"検証結果のパースに失敗しました: {e}"
        }, ensure_ascii=False))
        sys.exit(1)

    output = aggregate_results(results)
    print(json.dumps(output, ensure_ascii=False, indent=2))

    # 全て成功の場合のみ終了コード0
    sys.exit(0 if output["completed"] else 1)


if __name__ == "__main__":
    main()
