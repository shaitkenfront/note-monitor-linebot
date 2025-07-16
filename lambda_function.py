import json
from app import note_scraper, line_handler, db_handler, validator

def get_note_dashboard_response() -> str:
    """
    note.comのダッシュボード情報を取得し、整形された応答を返す
    """
    return note_scraper.get_note_dashboard_response()

def get_note_dashboard_response_for_user(note_username: str) -> str:
    """
    指定されたnote.comユーザーのダッシュボード情報を取得し、整形された応答を返す
    """
    return note_scraper.get_note_dashboard_response_for_user(note_username)

def handle_user_message(user_id: str, message: str) -> str:
    """
    ユーザーからのメッセージを処理する
    - note.comのユーザー名の場合：DynamoDBに保存
    - unfollow の場合：DynamoDBから削除
    - その他の場合：現在の登録情報を表示
    """
    db = db_handler.DynamoDBHandler()

    # アンフォローイベントの処理
    if message == 'unfollow':
        db.delete_user_mapping(user_id)
        return "User unregistered"

    # note.comのユーザー名として有効かチェック
    if validator.validate_note_username(message):
        # 登録数制限チェック（3個まで）
        current_count = db.count_user_mappings(user_id)
        current_usernames = db.get_user_mappings(user_id)

        # 既に同じユーザー名が登録されている場合はスキップ
        if message in current_usernames:
            return f"⚠️ 「{message}」は既に登録されています。"

        # 3個制限チェック
        if current_count >= 3:
            return "⚠️ 登録できるnoteユーザーIDは3個までです。"

        # DynamoDBに保存
        success = db.save_user_mapping(user_id, message)

        if success:
            return f"✅ note.comのユーザー名「{message}」を登録しました。\n定期的にフォロワー数の通知を送信します。"
        else:
            return "❌ 登録に失敗しました。しばらく経ってから再度お試しください。"
    else:
        # 現在の登録情報を表示
        current_usernames = db.get_user_mappings(user_id)

        if current_usernames:
            usernames_list = '\n'.join([f"• {username}" for username in current_usernames])
            return f"📊 現在の登録情報 ({len(current_usernames)}/3)\n\n👤 note.comユーザー名:\n{usernames_list}\n\n新しいユーザー名を登録する場合は、3-16文字の英数字とアンダースコアで入力してください。"
        else:
            return "📝 note.comのユーザー名を登録してください。\n\n例：hekisaya\n\n※ 3-16文字の英数字とアンダースコアのみ使用可能です。"

def lambda_handler(event, context):
    """
    AWS Lambdaのメインハンドラ関数。
    スケジュール実行またはLINEからのWebhookイベントを処理する。
    """
    # スケジュール実行の場合（EventBridgeからの呼び出し）
    if 'source' in event and event['source'] == 'aws.events':
        return handle_scheduled_execution(context)

    # API Gateway経由のLINEからのWebhookの場合
    if 'headers' in event and 'body' in event:
        return handle_line_webhook(event, context)

    return {
        'statusCode': 400,
        'body': json.dumps('Invalid event type')
    }

def handle_scheduled_execution(context):
    """
    スケジュール実行時の処理
    DynamoDBから全ユーザーを取得し、各ユーザーに対してnote.comの情報を送信
    """
    db = db_handler.DynamoDBHandler()

    # 全ユーザーマッピングを取得
    user_mappings = db.get_all_user_mappings()

    if not user_mappings:
        return {
            'statusCode': 200,
            'body': json.dumps('No registered users found')
        }

    # 各ユーザーに対してnote.comの情報を取得・送信
    for mapping in user_mappings:
        line_user_id = mapping['line_user_id']
        note_username = mapping['note_username']

        # note.comの情報を取得
        message = get_note_dashboard_response_for_user(note_username)

        # LINEで送信
        line_handler.send_push_message(line_user_id, message)

    return {
        'statusCode': 200,
        'body': json.dumps(f'Scheduled execution completed for {len(user_mappings)} users')
    }

def handle_line_webhook(event, context):
    """
    LINEからのWebhookイベントを処理
    - メッセージイベント：ユーザー名の登録・更新
    - アンフォローイベント：ユーザー情報の削除
    """
    signature = event['headers'].get('x-line-signature')
    body = event.get('body')

    if not signature:
        return {
            'statusCode': 400,
            'body': json.dumps('Missing X-Line-Signature')
        }

    if not body:
        return {
            'statusCode': 400,
            'body': json.dumps('Missing body')
        }

    # LINEイベント処理（ユーザー名の登録・削除処理）
    line_handler.handle_line_event(body, signature, handle_user_message)

    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }
