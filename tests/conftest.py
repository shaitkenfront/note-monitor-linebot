import pytest
import os
import sys

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def sample_note_url():
    """テスト用のnote.com URL"""
    return "https://note.com/test_user"

@pytest.fixture
def sample_html_with_followers():
    """フォロワー数が含まれたサンプルHTML"""
    return """
    <html>
    <head><title>Test User - note</title></head>
    <body>
        <div class="profile">
            <span class="followers-count">1,234</span>
            <span>フォロワー</span>
        </div>
    </body>
    </html>
    """

@pytest.fixture
def sample_html_without_followers():
    """フォロワー数が含まれていないサンプルHTML"""
    return """
    <html>
    <head><title>Test User - note</title></head>
    <body>
        <div class="profile">
            <span>プロフィール</span>
        </div>
    </body>
    </html>
    """

@pytest.fixture
def mock_environment_variables(monkeypatch):
    """テスト用の環境変数を設定"""
    monkeypatch.setenv('NOTE_URL', 'https://note.com/test_user')
    monkeypatch.setenv('LINE_CHANNEL_ACCESS_TOKEN', 'test_access_token')
    monkeypatch.setenv('LINE_CHANNEL_SECRET', 'test_channel_secret')
    monkeypatch.setenv('LINE_TARGET_ID', 'test_target_id')
    monkeypatch.setenv('DYNAMODB_TABLE_NAME', 'test-note-monitor-users')

@pytest.fixture
def sample_line_event():
    """LINE Webhookイベントのサンプル"""
    return {
        'events': [
            {
                'type': 'message',
                'replyToken': 'test_reply_token',
                'source': {
                    'userId': 'test_user_id'
                },
                'message': {
                    'type': 'text',
                    'text': 'テストメッセージ'
                }
            }
        ]
    }

@pytest.fixture
def sample_scheduled_event():
    """スケジュール実行イベントのサンプル"""
    return {
        'source': 'aws.events',
        'detail-type': 'Scheduled Event',
        'detail': {}
    }

@pytest.fixture
def sample_line_webhook_event():
    """LINE Webhookイベントのサンプル"""
    return {
        'headers': {
            'x-line-signature': 'test_signature'
        },
        'body': '{"events": [{"type": "message", "replyToken": "test_reply_token", "source": {"userId": "test_user_id"}, "message": {"type": "text", "text": "test"}}]}'
    }

@pytest.fixture
def sample_lambda_context():
    """Lambda contextのサンプル"""
    class MockContext:
        def __init__(self):
            self.function_name = 'test_function'
            self.function_version = '$LATEST'
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test_function'
            self.aws_request_id = 'test_request_id'
    
    return MockContext()