# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This project extracts Claude Code conversation history from `~/.claude/projects` and uploads it to AWS S3 or saves it locally.

**Location**: All tools are located in `.claude/astemo_utils/` to emphasize that these are Claude Code auxiliary utilities.

Main tools:
- `claude_history_uploader.py` - Basic version for simple extraction
- `enhanced_uploader.py` - Enhanced version with Git integration and commit filtering (recommended)

## Development Commands

### Testing

Run all tests:
```bash
python3 .claude/astemo_utils/test_commit_filter.py
python3 .claude/astemo_utils/test_git_integration.py
```

### Running the Tools

Basic uploader (save locally):
```bash
python3 .claude/astemo_utils/claude_history_uploader.py --output-dir=./output --project=<project-name>
```

Enhanced uploader (manual mode - specify commits):
```bash
python3 .claude/astemo_utils/enhanced_uploader.py \
  --output-dir=./output \
  --project=<project-name> \
  --repo-path=<path-to-git-repo> \
  --mode=manual \
  --before-commit=<start-commit-hash> \
  --after-commit=<end-commit-hash>
```

Enhanced uploader (latest mode - first commit to HEAD):
```bash
python3 .claude/astemo_utils/enhanced_uploader.py \
  --output-dir=./output \
  --project=<project-name> \
  --repo-path=<path-to-git-repo> \
  --mode=latest
```

Enhanced uploader (incremental mode - last uploaded to HEAD):
```bash
python3 .claude/astemo_utils/enhanced_uploader.py \
  --output-dir=./output \
  --project=<project-name> \
  --repo-path=<path-to-git-repo> \
  --mode=incremental
```

Note:
- Manual mode (default): --before-commit and --after-commit are REQUIRED
- Latest mode: Automatically uploads from first commit to HEAD (latest commit) and saves history
- Incremental mode: Uploads from last uploaded commit to HEAD (requires previous upload history)

For S3 upload with latest mode:
```bash
python3 .claude/astemo_utils/enhanced_uploader.py \
  --bucket=<s3-bucket-name> \
  --prefix=claude_logs \
  --project=<project-name> \
  --repo-path=<path-to-git-repo> \
  --mode=latest
```

Using config file for settings:
```bash
# Option 1: Copy from sample and edit
cp .claude/uploader_config.json.example .claude/uploader_config.json
# Then edit .claude/uploader_config.json to set your S3 bucket name

# Option 2: Create config file directly
cat > .claude/uploader_config.json <<EOF
{
  "s3": {
    "bucket": "claude-code-history",
    "prefix": "commit_base"
  },
  "project": {
    "name": "-home-ubuntu-agents-templete",
    "repo_path": "/home/ubuntu/agents-templete"
  }
}
EOF

# Upload using config file (no need to specify S3 settings, project, or repo-path)
python3 .claude/astemo_utils/enhanced_uploader.py \
  --mode=latest

# Or specify a custom config file location
python3 .claude/astemo_utils/enhanced_uploader.py \
  --config=/path/to/config.json \
  --mode=latest

# Override config values with command-line arguments
python3 .claude/astemo_utils/enhanced_uploader.py \
  --project=<different-project> \
  --repo-path=<different-path> \
  --mode=latest
```

Note: Files are uploaded to `s3://<bucket>/<prefix>/<project-name>/<commit-id>/<filename>.json`

Dry run mode (preview without saving):
```bash
python3 .claude/astemo_utils/enhanced_uploader.py \
  --output-dir=./output \
  --project=<project-name> \
  --repo-path=<path-to-git-repo> \
  --mode=latest \
  --dry-run
```

## Custom Commands

This project includes Claude Code custom commands for easy log uploading:

### `/upload-logs` - Incremental Upload
Commits changes (with user confirmation) and uploads logs from last upload to HEAD.

### `/upload-logs-latest` - Full Upload
Commits changes (with user confirmation) and uploads all logs from first commit to HEAD.

Both commands:
1. Check git status and show changed files
2. Ask: "変更をコミットしてログをアップロードしますか？ (y/n)"
3. If yes: ask for commit message and proceed with upload
4. If no: stop without committing or uploading

Commands are located in `.claude/commands/` directory.

## Hook Configuration

You can configure Claude Code to show a reminder at the end of each conversation.

Add this to `.claude/settings.local.json`:

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo '\n💡 会話が終了しました。変更をコミットしてログをアップロードする場合は /upload-logs を実行してください。'"
          }
        ]
      }
    ]
  }
}
```

This will display a reminder message when the conversation ends, prompting you to run `/upload-logs` if needed.

**Note**: `.claude/settings.local.json` is a personal settings file and is not tracked by git.

## Architecture

### Core Components

**ClaudeHistoryUploader** (`claude_history_uploader.py`)
- Reads `.jsonl` conversation files from `~/.claude/projects/<project-name>/`
- Extracts messages and metadata
- Saves to local files or uploads to S3
- Simple schema with basic metadata

**EnhancedHistoryUploader** (`enhanced_uploader.py`)
- Extends basic uploader with Git integration
- Filters conversations by commit timestamp range
- Generates rich metadata including Git stats, token usage, and I/O summaries
- Uses enhanced schema (see SCHEMA.md)

**GitInfo** (`enhanced_uploader.py`)
- Wrapper for Git operations
- Extracts commit timestamps, author info, and file changes
- Calculates diff statistics between commits
- Gets first commit and previous commit (HEAD~1) for automatic modes
- Used by EnhancedHistoryUploader for commit filtering

### Upload Modes

**Manual mode** (default)
- User specifies both `--before-commit` and `--after-commit`
- Full control over the commit range

**Latest mode**
- Automatically extracts from first commit to HEAD (latest commit)
- Saves upload history for incremental mode
- Ideal for regular automated uploads

**Incremental mode**
- Extracts from last uploaded commit to HEAD (latest commit)
- Only uploads new conversations since last upload
- Requires previous upload history from latest mode

### Configuration File

The enhanced uploader supports a JSON configuration file to specify S3 settings, project name, and repository path.

**Default location**: `.claude/uploader_config.json` (in project directory)

**Format**:
```json
{
  "s3": {
    "bucket": "claude-code-history",
    "prefix": "commit_base"
  },
  "project": {
    "name": "-home-ubuntu-agents-templete",
    "repo_path": "/home/ubuntu/agents-templete"
  }
}
```

**Configuration options**:
- `s3.bucket`: S3 bucket name for uploads
- `s3.prefix`: S3 key prefix (default: "claude_history")
- `project.name`: Project name (e.g., "-home-ubuntu-agents-templete")
- `project.repo_path`: Path to git repository

**Priority order** (highest to lowest):
1. Command-line arguments (`--bucket`, `--prefix`, `--project`, `--repo-path`)
2. Configuration file
3. Default values (for S3 prefix only)

**Note**: The config file is located in the project's `.claude/` directory, not in the user's home directory. This allows each project to have its own configuration.

**S3 Path Structure**:
Files are uploaded to: `s3://<bucket>/<prefix>/<project-name>/<commit-id>/<conversation-id>_<timestamp>.json`

Example: `s3://claude-code-history/commit_base/-home-ubuntu-agents-templete/0925167c3d15b54876313ff11cf31fa24e8236d2/daddead0-622a-4cf9-9197-9d5e4aacfb60_20251021_121446.json`

The `<commit-id>` is the after_commit (end of session commit) used for filtering.

### Commit Filtering Logic

The enhanced uploader filters conversation messages by timestamp:
1. `--before-commit`: Get timestamp of this commit → include messages AFTER this time
2. `--after-commit`: Get timestamp of this commit → include messages BEFORE this time
3. Filter messages: `before_commit_time <= message_time <= after_commit_time`

Upload history is stored in `~/.claude/upload_history/<project-name>.json`

### Output Schema

**Basic schema** (claude_history_uploader.py):
```json
{
  "project_name": "...",
  "conversation_id": "...",
  "message_count": N,
  "messages": [...]
}
```

**Enhanced schema** (enhanced_uploader.py):
```json
{
  "session": {
    "id": "uuid",
    "conversation_id": "...",
    "started_at": "...",
    "ended_at": "...",
    "duration_seconds": N
  },
  "data": {
    "conversation": {
      "messages": [...],
      "total_turns": N,
      "total_tokens": {...}
    },
    "git": {
      "commits": {"before": "...", "after": "..."},
      "branch": {...},
      "changes": {...}
    },
    "io_summary": {...}
  },
  "metadata": {
    "project": {...},
    "user": {...},
    "agent": {...},
    "environment": {...}
  }
}
```

See SCHEMA.md for complete schema documentation.

## Key Implementation Details

- Both uploaders support either S3 upload OR local file output (mutually exclusive)
- S3 functionality requires boto3 package; local output does not
- **Enhanced uploader has 3 modes: manual, latest, incremental**
- Manual mode requires --before-commit and --after-commit parameters
- Latest mode automatically uses first commit to HEAD (latest commit)
- Incremental mode automatically uses last uploaded commit to HEAD (latest commit)
- Incremental mode requires previous upload history from latest mode
- **Configuration file** (`~/.claude/uploader_config.json`) can specify S3 bucket and prefix
- Command-line arguments override config file settings
- S3 upload path: `s3://<bucket>/<prefix>/<project-name>/<commit-id>/<filename>.json`
- Local output path: `<output-dir>/<project-name>/<commit-id>/<filename>.json`
- The `<commit-id>` is the after_commit hash (end of session commit)
- Basic uploader (claude_history_uploader.py) extracts all conversations without filtering
- Project names follow pattern: `-home-ubuntu-<project-name>` (dash-separated path)
- Conversation files are `.jsonl` format with one JSON object per line
- Git commit filtering uses commit timestamps, not commit order
- Upload history stored in `~/.claude/upload_history/<project-name>.json`
- Test files create mock repositories and conversation data for validation
- Output files are named: `<conversation-id>_<timestamp>.json`

## Dependencies

- `boto3>=1.26.0` (only for S3 upload)
- `botocore>=1.29.0` (only for S3 upload)
- Python 3.6+ (uses f-strings, Path, subprocess)
