#!/usr/bin/env python3
"""
競合解決スクリプト
task-composerの静的解析結果からファイル競合を検出し、
依存関係を追加してtasks.jsonを更新する
"""

import json
import re
import sys


def main():
    # 競合情報を読み込み
    try:
        with open('conflicts.txt', 'r') as f:
            conflicts_text = f.read()
    except FileNotFoundError:
        print("conflicts.txt not found")
        sys.exit(0)

    # tasks.jsonを読み込み
    try:
        with open('tasks.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: tasks.json not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: JSON parse failed: {e}")
        sys.exit(1)

    if 'tasks' not in data or not isinstance(data['tasks'], list):
        print("Error: Invalid tasks.json structure")
        sys.exit(1)

    # 競合パターン（日本語/英語両対応）
    patterns = [
        r"タスク (\S+) と (\S+) が .+ (WriteWrite|WriteRead)",
        r"Task (\S+) and (\S+) have (WriteWrite|WriteRead)",
        r"(\S+)\s+と\s+(\S+).*(WriteWrite|WriteRead)",
        r"(\S+)\s+and\s+(\S+).*(WriteWrite|WriteRead)",
    ]

    resolved_count = 0

    for line in conflicts_text.strip().split('\n'):
        if not line.strip():
            continue

        match = None
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                break

        if match:
            task_a, task_b, conflict_type = match.groups()

            # 順序決定: タスクID辞書順で先のタスクを優先
            if task_a < task_b:
                prerequisite, dependent = task_a, task_b
            else:
                prerequisite, dependent = task_b, task_a

            print(f"解決 [{conflict_type}]: {dependent} に {prerequisite} への依存を追加")

            # dependentタスクにprerequisiteへの依存を追加
            task_found = False
            for task in data['tasks']:
                task_id = task.get('payload', {}).get('task_id', task.get('task_id', ''))
                if task_id == dependent:
                    task_found = True
                    if 'dependencies' not in task:
                        task['dependencies'] = []
                    if prerequisite not in task['dependencies']:
                        task['dependencies'].append(prerequisite)
                        resolved_count += 1
                    break

            if not task_found:
                print(f"⚠️ 警告: タスク {dependent} が見つかりません")

    # 更新したJSONを保存
    with open('tasks.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 依存関係を {resolved_count} 件追加しました")


if __name__ == "__main__":
    main()
