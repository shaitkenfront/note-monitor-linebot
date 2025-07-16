import os
import requests
import hmac
import hashlib
import base64
import json

# 環境変数からLINEの認証情報を取得
def get_line_credentials():
    access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
    channel_secret = os.environ.get('LINE_CHANNEL_SECRET')

    if not access_token or not channel_secret:
        print("LINE Channel Access Token or Channel Secret is not set in environment variables.")

    return access_token, channel_secret

LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET = get_line_credentials()

LINE_REPLY_API_URL = "https://api.line.me/v2/bot/message/reply"

def validate_signature(body: str, signature: str, channel_secret: str) -> bool:
    """
    LINEからのWebhookリクエストの署名を検証する。
    """
    hash = hmac.new(channel_secret.encode('utf-8'),
                    body.encode('utf-8'),
                    hashlib.sha256).digest()
    return hmac.compare_digest(signature.encode('utf-8'), base64.b64encode(hash))

def reply_message(reply_token: str, text: str):
    """
    LINE Messaging APIを使ってメッセージを返信する。
    """
    access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

    if not access_token:
        print("LINE Channel Access Token is not configured.")
        return

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    payload = {
        'replyToken': reply_token,
        'messages': [
            {
                'type': 'text',
                'text': text
            }
        ]
    }

    try:
        # ペイロードをUTF-8でエンコードして送信
        response = requests.post(LINE_REPLY_API_URL, headers=headers, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), timeout=5)
        response.raise_for_status()
        print(f"LINE reply API response: {response.status_code} {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error replying to LINE: {e}")

def send_push_message(target_id: str, text: str):
    """
    LINE Messaging APIを使ってプッシュメッセージを送信する。
    """
    access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

    if not access_token:
        print("LINE Channel Access Token is not configured.")
        return

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    payload = {
        'to': target_id,
        'messages': [
            {
                'type': 'text',
                'text': text
            }
        ]
    }

    push_url = "https://api.line.me/v2/bot/message/push"

    try:
        response = requests.post(push_url, headers=headers, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), timeout=5)
        response.raise_for_status()
        print(f"LINE push API response: {response.status_code} {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending push message to LINE: {e}")

def handle_line_event(event_body: str, signature: str, response_function):
    """
    LINEのWebhookイベントを処理し、応答関数を呼び出す。
    """
    channel_secret = os.environ.get('LINE_CHANNEL_SECRET')

    if not channel_secret:
        print("LINE Channel Secret is not configured.")
        return

    if not validate_signature(event_body, signature, channel_secret):
        print("Invalid signature. Please check your channel secret.")
        return

    events = json.loads(event_body)['events']
    for event in events:
        event_type = event['type']
        user_id = event['source']['userId']

        if event_type == 'message' and event['message']['type'] == 'text':
            reply_token = event['replyToken']
            user_message = event['message']['text']
            response_text = response_function(user_id, user_message)
            reply_message(reply_token, response_text)
        elif event_type == 'unfollow':
            # アンフォローイベントの処理
            response_function(user_id, 'unfollow')
            print(f"User {user_id} unfollowed the bot")
