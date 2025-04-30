# lambda/index.py
import json
import os
import re
import urllib.request
import urllib.error

# Lambda コンテキストからリージョンを抽出する関数（未使用だが、必要なら残す）
def extract_region_from_arn(arn):
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # Cognitoで認証されたユーザー情報を取得（必要に応じて利用）
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)

        # 会話履歴にユーザーメッセージを追加
        messages = conversation_history.copy()
        messages.append({
            "role": "user",
            "content": message
        })

        # FastAPIエンドポイント（環境変数で設定）
        # API_URL = os.environ["https://api-endpoint/chat"] 
        API_URL ="https://ddb4-34-13-199-5.ngrok-free.app"
        # FastAPIへPOSTリクエストを送信
        req = urllib.request.Request(
            url=API_URL,
            data=json.dumps({"prompt": message}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as res:
            body = res.read().decode("utf-8")
        response_body = json.loads(body)

        # FastAPI のレスポンス（例: {"reply": "..."})
        assistant_response = response_body.get("reply")
        if assistant_response is None:
            raise ValueError("Invalid response from API")

        # アシスタントの応答を履歴に追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })

        # 成功レスポンス
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }

    except Exception as error:
        print("Error:", str(error))

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
