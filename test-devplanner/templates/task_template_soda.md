# AIエージェント毎のタスク分解の例(Sodaのサブエージェント)
- タスクを分解する際に以下の情報を参考にする。

## AIエージェント種別
| Agent | Role | Writes to |
|-------|------|-----------|
| spec_writer | Requirements/specs | docs/ |
| test_writer | Tests (TDD Red) | tests/ |
| coder | Implementation (TDD Green) | src/ |
| reviewer | Code review | docs/review/ |
| doc_writer | Documentation | docs/ |

## AIエージェント毎のタスク例

### spec_writerのタスク例

```json
{
  "message_type": "TASK_ASSIGNMENT",
  "from_agent": "devplanner-agent",
  "to_agent": "spec_writer",
  "correlation_id": "issue-27-flow",
  "timestamp": "2025-11-04T03:00:00Z",
  "version": "1.0",
  "payload": {
    "task_id": "task-27-requirements",
    "task_type": "development",
    "issue_number": 27,
    "issue_title": "認証機能の実装",
    "agent_role": "spec_writer",
    "task_description": "JWT認証とセッション管理機能について、ユーザーのログイン・ログアウト・セッション管理・パスワードリセット機能の要件定義書作成、機能要件・非機能要件の整理、受け入れ基準の定義を行ってください。セキュリティ要件（認証強度、セッション管理、暗号化）と運用要件（ログ、監視、バックアップ）も含めて詳細に分析してください。",
    "repo_url": "https://github.com/org/repo",
    "output_dir": "AgentsDiv/Develop/",
    "base_branch": "feature/Claude-AI-Div",
    "interface_design": {
      "interface_name": "IAuthService",
      "methods": ["login", "logout", "validateToken"],
      "input_types": ["LoginRequest", "LogoutRequest"],
      "output_types": ["LoginResponse", "LogoutResponse"],
      "implementation_files": {
        "interface": "AgentsDiv/Develop/src/auth/IAuthService.h",
        "implementation": "AgentsDiv/Develop/src/auth/AuthService.cpp",
        "test": "AgentsDiv/Develop/tests/auth/AuthServiceTest.cpp"
      }
    }
  },
  "role": {
    "role_id": "spec_writer_role",
    "name": "Specification Writer",
    "file_permissions": {
      "allowed_paths": [
        "AgentsDiv/Develop/docs/",
        "AgentsDiv/Develop/requirements/"
      ],
      "read_only_paths": [
        "AgentsDiv/Develop/src/"
      ],
      "denied_paths": [
        ".env",
        "secrets/"
      ]
    }
  },
  "dependencies": [],
  "metadata": {
    "priority": "high",
    "retry_count": 0,
    "ttl_seconds": 3600
  }
}
```

### test_writerのタスク例

```json
{
  "message_type": "TASK_ASSIGNMENT",
  "from_agent": "devplanner-agent",
  "to_agent": "test_writer",
  "correlation_id": "issue-27-flow",
  "timestamp": "2025-11-04T03:00:00Z",
  "version": "1.0",
  "payload": {
    "task_id": "task-27-testing",
    "task_type": "development",
    "issue_number": 27,
    "issue_title": "認証機能の実装",
    "agent_role": "test_writer",
    "task_description": "認証機能のテストケースを作成する",
    "repo_url": "https://github.com/org/repo",
    "output_dir": "AgentsDiv/Develop/",
    "base_branch": "feature/Claude-AI-Div",
    "interface_design": {
      "interface_name": "IAuthService",
      "methods": ["login", "logout", "validateToken"],
      "implementation_files": {
        "test": "AgentsDiv/Develop/tests/auth/AuthServiceTest.cpp"
      }
    }
  },
  "role": {
    "role_id": "test_writer_role",
    "name": "Test Writer",
    "file_permissions": {
      "allowed_paths": [
        "AgentsDiv/Develop/tests/"
      ],
      "read_only_paths": [
        "AgentsDiv/Develop/src/",
        "AgentsDiv/Develop/docs/"
      ],
      "denied_paths": [
        ".env",
        "secrets/"
      ]
    }
  },
  "dependencies": ["task-27-requirements"],
  "metadata": {
    "priority": "high",
    "retry_count": 0,
    "ttl_seconds": 3600
  }
}
```

### coderのタスク例

```json
{
  "message_type": "TASK_ASSIGNMENT",
  "from_agent": "devplanner-agent",
  "to_agent": "coder",
  "correlation_id": "issue-27-flow",
  "timestamp": "2025-11-04T03:00:00Z",
  "version": "1.0",
  "payload": {
    "task_id": "task-27-coding",
    "task_type": "development",
    "issue_number": 27,
    "issue_title": "認証機能の実装",
    "agent_role": "coder",
    "task_description": "設計書に基づいてC++実装を行う",
    "repo_url": "https://github.com/org/repo",
    "output_dir": "AgentsDiv/Develop/",
    "base_branch": "feature/Claude-AI-Div",
    "interface_design": {
      "interface_name": "IAuthService",
      "methods": ["login", "logout", "validateToken"],
      "implementation_files": {
        "interface": "AgentsDiv/Develop/src/auth/IAuthService.h",
        "implementation": "AgentsDiv/Develop/src/auth/AuthService.cpp",
        "test": "AgentsDiv/Develop/tests/auth/AuthServiceTest.cpp"
      }
    }
  },
  "role": {
    "role_id": "coder_role",
    "name": "Code Developer",
    "file_permissions": {
      "allowed_paths": [
        "AgentsDiv/Develop/src/",
        "AgentsDiv/Develop/tests/"
      ],
      "read_only_paths": [
        "AgentsDiv/Develop/docs/",
        "AgentsDiv/Develop/requirements/"
      ],
      "denied_paths": [
        ".env",
        "secrets/"
      ]
    }
  },
  "dependencies": ["task-27-requirements"],
  "metadata": {
    "priority": "high",
    "retry_count": 0,
    "ttl_seconds": 3600
  }
}
```



### reviewerのタスク例

```json
{
  "message_type": "TASK_ASSIGNMENT",
  "from_agent": "devplanner-agent",
  "to_agent": "reviewer",
  "correlation_id": "issue-27-flow",
  "timestamp": "2025-11-04T03:00:00Z",
  "version": "1.0",
  "payload": {
    "task_id": "task-27-review",
    "task_type": "review",
    "issue_number": 27,
    "issue_title": "認証機能の実装",
    "agent_role": "reviewer",
    "task_description": "認証機能の実装コードとテストコードをレビューする",
    "repo_url": "https://github.com/org/repo",
    "output_dir": "AgentsDiv/Develop/",
    "base_branch": "feature/Claude-AI-Div"
  },
  "role": {
    "role_id": "reviewer_role",
    "name": "Code Reviewer",
    "file_permissions": {
      "allowed_paths": [
        "AgentsDiv/Develop/docs/review/"
      ],
      "read_only_paths": [
        "AgentsDiv/Develop/src/",
        "AgentsDiv/Develop/tests/",
        "AgentsDiv/Develop/docs/"
      ],
      "denied_paths": [
        ".env",
        "secrets/"
      ]
    }
  },
  "dependencies": ["task-27-coding", "task-27-testing"],
  "metadata": {
    "priority": "high",
    "retry_count": 0,
    "ttl_seconds": 3600
  }
}
```

### doc_writerのタスク例

```json
{
  "message_type": "TASK_ASSIGNMENT",
  "from_agent": "devplanner-agent",
  "to_agent": "doc_writer",
  "correlation_id": "issue-27-flow",
  "timestamp": "2025-11-04T03:00:00Z",
  "version": "1.0",
  "payload": {
    "task_id": "task-27-documentation",
    "task_type": "documentation",
    "issue_number": 27,
    "issue_title": "認証機能の実装",
    "agent_role": "doc_writer",
    "task_description": "認証機能のドキュメントを作成する",
    "repo_url": "https://github.com/org/repo",
    "output_dir": "AgentsDiv/Develop/",
    "base_branch": "feature/Claude-AI-Div"
  },
  "role": {
    "role_id": "doc_writer_role",
    "name": "Documentation Writer",
    "file_permissions": {
      "allowed_paths": [
        "AgentsDiv/Develop/docs/"
      ],
      "read_only_paths": [
        "AgentsDiv/Develop/src/",
        "AgentsDiv/Develop/tests/"
      ],
      "denied_paths": [
        ".env",
        "secrets/"
      ]
    }
  },
  "dependencies": ["task-27-review"],
  "metadata": {
    "priority": "medium",
    "retry_count": 0,
    "ttl_seconds": 3600
  }
}
```
