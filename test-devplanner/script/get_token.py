#!/usr/bin/env python3
"""Cognito認証トークン取得スクリプト（boto3不要版）

Soda Remote MCPサーバーへの認証に使用するJWTトークンを取得します。
標準ライブラリのみで動作するため、追加の依存関係は不要です。

使用方法:
    # 環境変数を設定
    export COGNITO_USERNAME="your_username"
    export COGNITO_PASSWORD="your_password"

    # トークン取得（標準出力）
    python .github/script/get_token.py

    # 環境変数としてエクスポート
    eval $(python .github/script/get_token.py --export)

環境変数（オプション）:
    COGNITO_REGION       : Cognitoリージョン（デフォルト: us-east-1）
    COGNITO_USER_POOL_ID : User Pool ID（デフォルト: us-east-1_XGh45d63R）
    COGNITO_CLIENT_ID    : App Client ID（デフォルト: 6jik83k77et8gvts525eiaulv2）
    SODA_MCP_SECRET      : Client Secret（Confidential Clientの場合のみ）
    COGNITO_TIMEOUT      : リクエストタイムアウト秒数（デフォルト: 30）
    COGNITO_MAX_RETRIES  : 最大リトライ回数（デフォルト: 3）
"""

import os
import sys
import json
import hmac
import hashlib
import base64
import time
import urllib.request
import urllib.error

# Cognito設定（環境変数で上書き可能）
COGNITO_REGION = os.environ.get("COGNITO_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "us-east-1_XGh45d63R")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "6jik83k77et8gvts525eiaulv2")
COGNITO_ENDPOINT = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/"

# タイムアウトとリトライ設定
DEFAULT_TIMEOUT = int(os.environ.get("COGNITO_TIMEOUT", "30"))
DEFAULT_MAX_RETRIES = int(os.environ.get("COGNITO_MAX_RETRIES", "3"))


def compute_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Confidential Client用のSECRET_HASHを計算

    Args:
        username: Cognitoユーザー名
        client_id: Cognito App Client ID
        client_secret: Cognito App Client Secret

    Returns:
        Base64エンコードされたSECRET_HASH
    """
    message = username + client_id
    dig = hmac.new(
        client_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()


def get_cognito_token(
    username: str,
    password: str,
    client_secret: str = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Cognito USER_PASSWORD_AUTH フローでトークンを取得

    Args:
        username: Cognitoユーザー名
        password: Cognitoパスワード
        client_secret: Client Secret（Confidential Clientの場合のみ）
        timeout: リクエストタイムアウト（秒）

    Returns:
        トークン情報を含む辞書:
        - access_token: アクセストークン
        - id_token: IDトークン
        - expires_in: 有効期限（秒）

    Raises:
        urllib.error.HTTPError: HTTP通信エラー時
        urllib.error.URLError: ネットワークエラー時
    """
    auth_params = {
        "USERNAME": username,
        "PASSWORD": password,
    }

    # Confidential Client の場合は SECRET_HASH が必要
    if client_secret:
        auth_params["SECRET_HASH"] = compute_secret_hash(
            username, COGNITO_CLIENT_ID, client_secret
        )

    payload = {
        "AuthFlow": "USER_PASSWORD_AUTH",
        "ClientId": COGNITO_CLIENT_ID,
        "AuthParameters": auth_params,
    }

    req = urllib.request.Request(
        COGNITO_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
        },
    )

    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
        result = data["AuthenticationResult"]
        return {
            "access_token": result.get("AccessToken"),
            "id_token": result.get("IdToken"),
            "expires_in": result.get("ExpiresIn", 3600),
        }


def get_cognito_token_with_retry(
    username: str,
    password: str,
    client_secret: str = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> dict:
    """リトライ機能付きでCognitoトークンを取得

    一時的なネットワークエラーやサーバーエラー（5xx）の場合、
    指数バックオフでリトライを行います。

    Args:
        username: Cognitoユーザー名
        password: Cognitoパスワード
        client_secret: Client Secret（Confidential Clientの場合のみ）
        timeout: リクエストタイムアウト（秒）
        max_retries: 最大リトライ回数

    Returns:
        トークン情報を含む辞書

    Raises:
        SystemExit: 全リトライ失敗時
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            return get_cognito_token(username, password, client_secret, timeout)

        except urllib.error.HTTPError as e:
            last_error = e
            error_body = e.read().decode("utf-8")

            # クライアントエラー（4xx）はリトライしない
            if 400 <= e.code < 500:
                print(f"Error: {e.code} - {error_body}", file=sys.stderr)
                sys.exit(1)

            # サーバーエラー（5xx）はリトライ
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1, 2, 4秒...
                print(
                    f"Server error ({e.code}), retrying in {wait_time}s... "
                    f"(attempt {attempt + 1}/{max_retries})",
                    file=sys.stderr,
                )
                time.sleep(wait_time)
            else:
                print(
                    f"Error after {max_retries} retries: {e.code} - {error_body}",
                    file=sys.stderr,
                )
                sys.exit(1)

        except urllib.error.URLError as e:
            last_error = e
            # ネットワークエラーはリトライ
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(
                    f"Network error ({e.reason}), retrying in {wait_time}s... "
                    f"(attempt {attempt + 1}/{max_retries})",
                    file=sys.stderr,
                )
                time.sleep(wait_time)
            else:
                print(
                    f"Network error after {max_retries} retries: {e.reason}",
                    file=sys.stderr,
                )
                sys.exit(1)

        except TimeoutError:
            last_error = TimeoutError(f"Request timed out after {timeout}s")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(
                    f"Timeout, retrying in {wait_time}s... "
                    f"(attempt {attempt + 1}/{max_retries})",
                    file=sys.stderr,
                )
                time.sleep(wait_time)
            else:
                print(
                    f"Timeout after {max_retries} retries",
                    file=sys.stderr,
                )
                sys.exit(1)

    # ここには到達しないはず
    print(f"Unexpected error: {last_error}", file=sys.stderr)
    sys.exit(1)


def main():
    """メイン関数"""
    username = os.environ.get("COGNITO_USERNAME")
    password = os.environ.get("COGNITO_PASSWORD")
    client_secret = os.environ.get("SODA_MCP_SECRET")  # オプション

    if not username or not password:
        print("Error: COGNITO_USERNAME and COGNITO_PASSWORD are required", file=sys.stderr)
        print("", file=sys.stderr)
        print("Usage:", file=sys.stderr)
        print("  export COGNITO_USERNAME='your_username'", file=sys.stderr)
        print("  export COGNITO_PASSWORD='your_password'", file=sys.stderr)
        print("  python .github/script/get_token.py [--export]", file=sys.stderr)
        print("", file=sys.stderr)
        print("Optional environment variables:", file=sys.stderr)
        print("  COGNITO_REGION       : Cognito region (default: us-east-1)", file=sys.stderr)
        print("  COGNITO_USER_POOL_ID : User Pool ID", file=sys.stderr)
        print("  COGNITO_CLIENT_ID    : App Client ID", file=sys.stderr)
        print("  SODA_MCP_SECRET      : Client Secret (for confidential clients)", file=sys.stderr)
        print("  COGNITO_TIMEOUT      : Request timeout in seconds (default: 30)", file=sys.stderr)
        print("  COGNITO_MAX_RETRIES  : Max retry attempts (default: 3)", file=sys.stderr)
        sys.exit(1)

    tokens = get_cognito_token_with_retry(username, password, client_secret)
    token = tokens["access_token"]

    if "--export" in sys.argv:
        print(f'export SODA_TOKEN="{token}"')
    else:
        print(token)


if __name__ == "__main__":
    main()
