#!/usr/bin/env python3
"""
Soda Remote MCPを直接呼び出すスクリプト

task-composerのbash_executorから呼び出される
改修案2: claude_code_mcp経由ではなく、直接Soda Remote MCPを呼び出す
"""

import base64
import hashlib
import hmac
import json
import os
import sys
import time
import traceback

import boto3
import requests


# 環境変数から設定を読み込み
REGION = os.environ.get("SODA_MCP_REGION", "ap-northeast-1")
RUNTIME_ID = os.environ.get("SODA_MCP_RUNTIME_ID")  # 必須
QUALIFIER = os.environ.get("SODA_MCP_QUALIFIER", "")  # オプション（例: DEFAULT, LIVE）

# Cognito認証設定
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.environ.get("COGNITO_CLIENT_SECRET")  # Confidential Client用
COGNITO_USERNAME = os.environ.get("COGNITO_USERNAME")
COGNITO_PASSWORD = os.environ.get("COGNITO_PASSWORD")

# Cognitoリージョン: COGNITO_USER_POOL_IDから抽出（形式: us-east-1_XGh45d63R）
# SODA_MCP_REGIONとは異なるリージョンの可能性があるため、別途設定
def get_cognito_region() -> str:
    """COGNITO_USER_POOL_IDからリージョンを抽出"""
    if COGNITO_USER_POOL_ID and "_" in COGNITO_USER_POOL_ID:
        return COGNITO_USER_POOL_ID.split("_")[0]
    # フォールバック: 明示的に指定されていればそれを使用、なければus-east-1
    return os.environ.get("COGNITO_REGION", "us-east-1")

COGNITO_REGION = get_cognito_region()

# タイムアウト設定
CONNECT_TIMEOUT = int(os.environ.get("SODA_CONNECT_TIMEOUT", "120"))
READ_TIMEOUT = int(os.environ.get("SODA_READ_TIMEOUT", "1800"))  # 30分


def calculate_secret_hash(username: str) -> str:
    """Cognito認証用のSECRET_HASHを計算

    Confidential Clientの場合に必要。
    SECRET_HASH = Base64(HMAC_SHA256(client_secret, username + client_id))

    Returns:
        str: SECRET_HASH、またはCLIENT_SECRETが未設定の場合はNone
    """
    if not COGNITO_CLIENT_SECRET:
        return None

    message = username + COGNITO_CLIENT_ID
    dig = hmac.new(
        COGNITO_CLIENT_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()


def get_cognito_token() -> str:
    """Cognitoからアクセストークンを取得"""
    if not COGNITO_CLIENT_ID:
        raise ValueError("COGNITO_CLIENT_ID environment variable is required")
    if not COGNITO_USERNAME:
        raise ValueError("COGNITO_USERNAME environment variable is required")
    if not COGNITO_PASSWORD:
        raise ValueError("COGNITO_PASSWORD environment variable is required")

    # CognitoはSODA_MCP_REGIONとは異なるリージョンの可能性があるため、
    # COGNITO_USER_POOL_IDから抽出したCOGNITO_REGIONを使用
    print(f"[soda_invoker] Cognito region: {COGNITO_REGION}", file=sys.stderr)
    client = boto3.client("cognito-idp", region_name=COGNITO_REGION)

    # 認証パラメータを構築
    auth_params = {
        "USERNAME": COGNITO_USERNAME,
        "PASSWORD": COGNITO_PASSWORD,
    }

    # Confidential Clientの場合はSECRET_HASHを追加
    secret_hash = calculate_secret_hash(COGNITO_USERNAME)
    if secret_hash:
        auth_params["SECRET_HASH"] = secret_hash
        print(f"[soda_invoker] Using SECRET_HASH for confidential client", file=sys.stderr)

    response = client.initiate_auth(
        ClientId=COGNITO_CLIENT_ID,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters=auth_params
    )
    return response["AuthenticationResult"]["AccessToken"]


def invoke_soda(
    prompt: str,
    repo_url: str,
    branch: str,
    subagent: str,
    auto_commit: bool = True,
    auto_push: bool = True,
    include_history: bool = False,
    file_permissions: dict = None,
) -> dict:
    """Soda Remote MCPのinvoke_sodaを呼び出す

    注意: output_dirはinvoke_sodaのパラメータではないため、
    作業ディレクトリの指定はprompt内に含めること

    Args:
        file_permissions: ファイル権限設定（オプション）
            - allowed_paths: 書き込み許可パスのリスト
            - settings.local.jsonよりも優先される
    """

    if not RUNTIME_ID:
        raise ValueError("SODA_MCP_RUNTIME_ID environment variable is required")

    print(f"[soda_invoker] Starting invoke_soda", file=sys.stderr)
    print(f"[soda_invoker] repo_url: {repo_url}", file=sys.stderr)
    print(f"[soda_invoker] branch: {branch}", file=sys.stderr)
    print(f"[soda_invoker] subagent: {subagent}", file=sys.stderr)
    if file_permissions:
        print(f"[soda_invoker] file_permissions: {file_permissions}", file=sys.stderr)

    # Cognito認証
    print(f"[soda_invoker] Getting Cognito token...", file=sys.stderr)
    start_auth = time.time()
    token = get_cognito_token()
    print(f"[soda_invoker] Cognito token obtained in {time.time() - start_auth:.2f}s", file=sys.stderr)

    # MCP呼び出し
    url = f"https://bedrock-agentcore.{REGION}.amazonaws.com/runtimes/{RUNTIME_ID}/invocations"
    if QUALIFIER:
        url = f"{url}?qualifier={QUALIFIER}"
    print(f"[soda_invoker] Calling MCP endpoint: {url}", file=sys.stderr)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"  # MCPプロトコル必須
    }

    # MCP arguments構築
    arguments = {
        "prompt": prompt,
        "repo_url": repo_url,
        "source_branch": branch,  # branch → source_branch へマッピング
        "subagent": subagent,
        "auto_commit": auto_commit,
        "auto_push": auto_push,
        "include_history": include_history,
    }

    # file_permissionsが指定されている場合のみ追加
    if file_permissions:
        arguments["file_permissions"] = file_permissions

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "invoke_soda",
            "arguments": arguments
        },
        "id": 1
    }

    start_call = time.time()
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
        )
        elapsed = time.time() - start_call
        print(f"[soda_invoker] MCP call completed in {elapsed:.2f}s", file=sys.stderr)
        print(f"[soda_invoker] HTTP status: {response.status_code}", file=sys.stderr)

        if response.status_code != 200:
            print(f"[soda_invoker] Error response: {response.text}", file=sys.stderr)
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}",
                "detail": response.text
            }

        # デバッグ出力: レスポンスの詳細を確認
        content_type = response.headers.get('Content-Type', 'unknown')
        print(f"[soda_invoker] Response Content-Type: {content_type}", file=sys.stderr)
        print(f"[soda_invoker] Response length: {len(response.text)} bytes", file=sys.stderr)

        # 空レスポンスのチェック
        if not response.text:
            print(f"[soda_invoker] Warning: Empty response body", file=sys.stderr)
            return {
                "status": "error",
                "error": "empty_response",
                "detail": "MCP server returned empty response body"
            }

        # レスポンス内容のデバッグ出力（先頭500文字）
        print(f"[soda_invoker] Response text (first 500 chars): {response.text[:500]}", file=sys.stderr)

        # レスポンスのパース（SSE形式対応）
        result = None
        if 'text/event-stream' in content_type:
            # SSE形式: "event: message\r\ndata: {...}\r\n\r\n"
            print(f"[soda_invoker] Parsing SSE format response", file=sys.stderr)
            for line in response.text.replace('\r\n', '\n').split('\n'):
                line = line.strip()
                if line.startswith('data: '):
                    json_str = line[6:]  # "data: " を除去
                    try:
                        result = json.loads(json_str)
                        print(f"[soda_invoker] SSE data parsed successfully", file=sys.stderr)
                        break
                    except json.JSONDecodeError:
                        continue
            if result is None:
                print(f"[soda_invoker] Failed to parse any SSE data line", file=sys.stderr)
                return {
                    "status": "error",
                    "error": "sse_parse_error",
                    "detail": "Failed to parse SSE response",
                    "raw_response": response.text[:1000]
                }
        else:
            # 通常のJSON形式
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                print(f"[soda_invoker] JSON parse error: {e}", file=sys.stderr)
                return {
                    "status": "error",
                    "error": "json_parse_error",
                    "detail": str(e),
                    "raw_response": response.text[:1000]
                }

        # JSON-RPCレベルのエラーチェック
        if "error" in result:
            error_info = result["error"]
            print(f"[soda_invoker] JSON-RPC error: {error_info}", file=sys.stderr)
            return {
                "status": "error",
                "error": "jsonrpc_error",
                "detail": error_info.get("message", str(error_info)),
                "code": error_info.get("code")
            }

        # MCPレベルの結果確認
        mcp_result = result.get("result", {})
        if mcp_result.get("isError"):
            content = mcp_result.get("content", [])
            error_text = content[0].get("text", "Unknown error") if content else "Unknown error"
            print(f"[soda_invoker] MCP error: {error_text}", file=sys.stderr)
            return {
                "status": "error",
                "error": "mcp_error",
                "detail": error_text
            }

        print(f"[soda_invoker] Response received successfully", file=sys.stderr)
        return result

    except requests.exceptions.Timeout as e:
        elapsed = time.time() - start_call
        print(f"[soda_invoker] Timeout after {elapsed:.2f}s: {e}", file=sys.stderr)
        return {
            "status": "error",
            "error": "timeout",
            "detail": str(e)
        }
    except requests.exceptions.RequestException as e:
        print(f"[soda_invoker] Request error: {e}", file=sys.stderr)
        return {
            "status": "error",
            "error": "request_error",
            "detail": str(e)
        }


def main():
    """メインエントリーポイント"""
    if len(sys.argv) < 2:
        print("Usage: soda_invoker.py [--base64] '<json_params_or_base64>'", file=sys.stderr)
        print("  --base64: パラメータがBase64エンコードされていることを示す", file=sys.stderr)
        sys.exit(1)

    try:
        # コマンドライン引数からパラメータを読み込み
        # --base64オプションがある場合はBase64デコードを行う
        if len(sys.argv) >= 3 and sys.argv[1] == "--base64":
            # Base64エンコードされたJSONをデコード
            params_b64 = sys.argv[2]
            params_json = base64.b64decode(params_b64).decode('utf-8')
            params = json.loads(params_json)
            print(f"[soda_invoker] Parameters (decoded from base64): {params_json[:200]}...", file=sys.stderr)
        else:
            # 直接JSONとしてパース
            params = json.loads(sys.argv[1])
            print(f"[soda_invoker] Parameters: {json.dumps(params, ensure_ascii=False)[:200]}...", file=sys.stderr)

        result = invoke_soda(**params)

        # 結果を標準出力にJSON形式で出力
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # エラー結果の場合はexit code 1で終了（task-composerがFAILED判定できるように）
        if result.get("status") == "error":
            print(f"[soda_invoker] Exiting with error status", file=sys.stderr)
            sys.exit(1)

        # 正常終了時は明示的にexit code 0で終了
        print(f"[soda_invoker] Completed successfully", file=sys.stderr)
        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"[soda_invoker] JSON parse error: {e}", file=sys.stderr)
        error_result = {
            "status": "error",
            "error": "json_parse_error",
            "detail": str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)
    except Exception as e:
        print(f"[soda_invoker] Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        error_result = {
            "status": "error",
            "error": "unexpected_error",
            "detail": str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == "__main__":
    main()
