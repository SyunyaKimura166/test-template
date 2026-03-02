#!/usr/bin/env python3
"""成果物検証スクリプト

DevPlannerのタスク実行後に、期待される成果物が作成されたかを検証する。
task-composerのBashExecutorから呼び出され、JSON形式で結果を出力する。

Usage:
    python3 validate_output.py --expected-files '["file1.py", "file2.py"]' \
                               --expected-dirs '["src/", "tests/"]' \
                               --output-dir /path/to/project

Output:
    JSON形式で検証結果を標準出力に出力
    task-composerのBashExecutorは出力をパースして output.parsed で参照可能

Exit Code:
    0: 全ての成果物が存在（completed=true）
    1: 一部または全ての成果物が欠落（completed=false）
"""
import argparse
import json
import os
import sys


def validate(expected_files: list, expected_dirs: list, output_dir: str) -> dict:
    """成果物の存在を検証する

    Args:
        expected_files: 期待されるファイルのリスト（output_dirからの相対パス）
        expected_dirs: 期待されるディレクトリのリスト（output_dirからの相対パス）
        output_dir: 検証対象のルートディレクトリ

    Returns:
        検証結果を含む辞書
        {
            "completed": bool,           # 全ての成果物が存在するか
            "missing_files": list,       # 欠落しているファイル
            "missing_directories": list, # 欠落しているディレクトリ
            "found_files": list,         # 存在が確認されたファイル
            "found_directories": list,   # 存在が確認されたディレクトリ
            "errors": list               # エラーメッセージ（フィードバック用）
        }
    """
    result = {
        "completed": True,
        "missing_files": [],
        "missing_directories": [],
        "found_files": [],
        "found_directories": [],
        "errors": []
    }

    # output_dirの正規化
    if output_dir:
        output_dir = os.path.abspath(output_dir)
    else:
        output_dir = os.getcwd()

    # ファイル存在チェック
    for f in expected_files:
        # 相対パスをoutput_dirと結合
        if os.path.isabs(f):
            path = f
        else:
            path = os.path.join(output_dir, f)

        if os.path.isfile(path):
            result["found_files"].append(f)
        else:
            result["completed"] = False
            result["missing_files"].append(f)
            result["errors"].append(f"ファイル未作成: {f}")

    # ディレクトリ存在チェック
    for d in expected_dirs:
        # 相対パスをoutput_dirと結合
        if os.path.isabs(d):
            path = d
        else:
            path = os.path.join(output_dir, d)

        if os.path.isdir(path):
            result["found_directories"].append(d)
        else:
            result["completed"] = False
            result["missing_directories"].append(d)
            result["errors"].append(f"ディレクトリ未作成: {d}")

    # サマリー情報を追加
    total_files = len(expected_files)
    total_dirs = len(expected_dirs)
    found_files = len(result["found_files"])
    found_dirs = len(result["found_directories"])

    result["summary"] = {
        "total_expected_files": total_files,
        "total_expected_directories": total_dirs,
        "found_files_count": found_files,
        "found_directories_count": found_dirs,
        "missing_files_count": len(result["missing_files"]),
        "missing_directories_count": len(result["missing_directories"]),
        "completion_rate": (
            (found_files + found_dirs) / (total_files + total_dirs) * 100
            if (total_files + total_dirs) > 0 else 100.0
        )
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="成果物検証スクリプト - DevPlannerタスクの成果物存在確認",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 基本的な使用方法
  python3 validate_output.py \\
    --expected-files '["src/main.py", "tests/test_main.py"]' \\
    --expected-dirs '["src/", "tests/"]' \\
    --output-dir ./my_project

  # task-composerからの呼び出し例
  python3 validate_output.py \\
    --expected-files '${EXPECTED_FILES}' \\
    --output-dir '${OUTPUT_DIR}'
        """
    )
    parser.add_argument(
        "--expected-files",
        type=str,
        default="[]",
        help="期待されるファイルのJSONリスト (例: '[\"src/main.py\"]')"
    )
    parser.add_argument(
        "--expected-dirs",
        type=str,
        default="[]",
        help="期待されるディレクトリのJSONリスト (例: '[\"src/\", \"tests/\"]')"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="検証対象のルートディレクトリ (デフォルト: カレントディレクトリ)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="詳細な出力を表示"
    )

    args = parser.parse_args()

    # JSON引数のパース
    try:
        expected_files = json.loads(args.expected_files)
        if not isinstance(expected_files, list):
            raise ValueError("expected-files must be a JSON array")
    except json.JSONDecodeError as e:
        error_result = {
            "completed": False,
            "errors": [f"expected-files JSON parse error: {e}"],
            "missing_files": [],
            "missing_directories": [],
            "found_files": [],
            "found_directories": []
        }
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)

    try:
        expected_dirs = json.loads(args.expected_dirs)
        if not isinstance(expected_dirs, list):
            raise ValueError("expected-dirs must be a JSON array")
    except json.JSONDecodeError as e:
        error_result = {
            "completed": False,
            "errors": [f"expected-dirs JSON parse error: {e}"],
            "missing_files": [],
            "missing_directories": [],
            "found_files": [],
            "found_directories": []
        }
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)

    # 検証実行
    result = validate(expected_files, expected_dirs, args.output_dir)

    # 結果出力
    if args.verbose:
        # 詳細出力（人間が読みやすい形式）
        print("=" * 60, file=sys.stderr)
        print("成果物検証結果", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(f"検証ディレクトリ: {os.path.abspath(args.output_dir)}", file=sys.stderr)
        print(f"完了状態: {'✅ 完了' if result['completed'] else '❌ 未完了'}", file=sys.stderr)
        print(f"達成率: {result['summary']['completion_rate']:.1f}%", file=sys.stderr)

        if result["found_files"]:
            print("\n✅ 作成済みファイル:", file=sys.stderr)
            for f in result["found_files"]:
                print(f"  - {f}", file=sys.stderr)

        if result["missing_files"]:
            print("\n❌ 未作成ファイル:", file=sys.stderr)
            for f in result["missing_files"]:
                print(f"  - {f}", file=sys.stderr)

        if result["found_directories"]:
            print("\n✅ 作成済みディレクトリ:", file=sys.stderr)
            for d in result["found_directories"]:
                print(f"  - {d}", file=sys.stderr)

        if result["missing_directories"]:
            print("\n❌ 未作成ディレクトリ:", file=sys.stderr)
            for d in result["missing_directories"]:
                print(f"  - {d}", file=sys.stderr)

        print("=" * 60, file=sys.stderr)
        print("\nJSON出力:", file=sys.stderr)

    # JSON出力（task-composerがパースする）
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 終了コード: 欠落があれば1、なければ0
    sys.exit(0 if result["completed"] else 1)


if __name__ == "__main__":
    main()
