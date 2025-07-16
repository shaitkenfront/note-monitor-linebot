import pytest
import json
import hmac
import hashlib
import base64
import requests
from unittest.mock import patch, Mock
from app import line_handler


class TestLineHandler:
    
    def test_get_line_credentials_success(self, mock_environment_variables):
        """環境変数から認証情報を正しく取得できること"""
        access_token, channel_secret = line_handler.get_line_credentials()
        
        assert access_token == 'test_access_token'
        assert channel_secret == 'test_channel_secret'
    
    def test_get_line_credentials_missing_token(self, monkeypatch):
        """アクセストークンが設定されていない場合"""
        monkeypatch.delenv('LINE_CHANNEL_ACCESS_TOKEN', raising=False)
        monkeypatch.setenv('LINE_CHANNEL_SECRET', 'test_channel_secret')
        
        access_token, channel_secret = line_handler.get_line_credentials()
        
        assert access_token is None
        assert channel_secret == 'test_channel_secret'
    
    def test_get_line_credentials_missing_secret(self, monkeypatch):
        """チャンネルシークレットが設定されていない場合"""
        monkeypatch.setenv('LINE_CHANNEL_ACCESS_TOKEN', 'test_access_token')
        monkeypatch.delenv('LINE_CHANNEL_SECRET', raising=False)
        
        access_token, channel_secret = line_handler.get_line_credentials()
        
        assert access_token == 'test_access_token'
        assert channel_secret is None
    
    def test_validate_signature_success(self):
        """正しい署名の検証が成功すること"""
        body = "test body"
        channel_secret = "test_secret"
        
        # 正しい署名を生成
        hash_value = hmac.new(
            channel_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature = base64.b64encode(hash_value).decode('utf-8')
        
        result = line_handler.validate_signature(body, signature, channel_secret)
        
        assert result is True
    
    def test_validate_signature_failure(self):
        """間違った署名の検証が失敗すること"""
        body = "test body"
        channel_secret = "test_secret"
        wrong_signature = "wrong_signature"
        
        result = line_handler.validate_signature(body, wrong_signature, channel_secret)
        
        assert result is False
    
    @patch('requests.post')
    def test_reply_message_success(self, mock_post, mock_environment_variables):
        """メッセージ返信が正常に動作すること"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        line_handler.reply_message("test_reply_token", "test message")
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        assert args[0] == line_handler.LINE_REPLY_API_URL
        assert kwargs['headers']['Authorization'] == 'Bearer test_access_token'
        assert kwargs['headers']['Content-Type'] == 'application/json'
        
        # ペイロードの内容を確認
        payload = json.loads(kwargs['data'].decode('utf-8'))
        assert payload['replyToken'] == 'test_reply_token'
        assert payload['messages'][0]['type'] == 'text'
        assert payload['messages'][0]['text'] == 'test message'
    
    @patch('requests.post')
    def test_reply_message_request_error(self, mock_post, mock_environment_variables):
        """リクエストエラーが発生した場合も正常に処理されること"""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        # エラーが発生しても例外が発生しないことを確認
        line_handler.reply_message("test_reply_token", "test message")
        
        mock_post.assert_called_once()
    
    def test_reply_message_no_access_token(self, monkeypatch):
        """アクセストークンが設定されていない場合"""
        monkeypatch.delenv('LINE_CHANNEL_ACCESS_TOKEN', raising=False)
        
        # エラーが発生しても例外が発生しないことを確認
        line_handler.reply_message("test_reply_token", "test message")
    
    @patch('requests.post')
    def test_send_push_message_success(self, mock_post, mock_environment_variables):
        """プッシュメッセージ送信が正常に動作すること"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        line_handler.send_push_message("test_target_id", "test message")
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        assert args[0] == "https://api.line.me/v2/bot/message/push"
        assert kwargs['headers']['Authorization'] == 'Bearer test_access_token'
        assert kwargs['headers']['Content-Type'] == 'application/json'
        
        # ペイロードの内容を確認
        payload = json.loads(kwargs['data'].decode('utf-8'))
        assert payload['to'] == 'test_target_id'
        assert payload['messages'][0]['type'] == 'text'
        assert payload['messages'][0]['text'] == 'test message'
    
    @patch('requests.post')
    def test_send_push_message_request_error(self, mock_post, mock_environment_variables):
        """プッシュメッセージ送信でリクエストエラーが発生した場合"""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        # エラーが発生しても例外が発生しないことを確認
        line_handler.send_push_message("test_target_id", "test message")
        
        mock_post.assert_called_once()
    
    def test_send_push_message_no_access_token(self, monkeypatch):
        """プッシュメッセージ送信でアクセストークンが設定されていない場合"""
        monkeypatch.delenv('LINE_CHANNEL_ACCESS_TOKEN', raising=False)
        
        # エラーが発生しても例外が発生しないことを確認
        line_handler.send_push_message("test_target_id", "test message")
    
    @patch('app.line_handler.reply_message')
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_success(self, mock_validate, mock_reply, mock_environment_variables):
        """LINEイベント処理が正常に動作すること"""
        mock_validate.return_value = True
        mock_response_function = Mock(return_value="response message")
        
        event_body = json.dumps({
            'events': [
                {
                    'type': 'message',
                    'replyToken': 'test_reply_token',
                    'source': {
                        'userId': 'test_user_id'
                    },
                    'message': {
                        'type': 'text',
                        'text': 'test message'
                    }
                }
            ]
        })
        
        line_handler.handle_line_event(event_body, "test_signature", mock_response_function)
        
        mock_validate.assert_called_once_with(event_body, "test_signature", "test_channel_secret")
        mock_response_function.assert_called_once_with("test_user_id", "test message")
        mock_reply.assert_called_once_with("test_reply_token", "response message")
    
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_invalid_signature(self, mock_validate, mock_environment_variables):
        """無効な署名の場合は処理が停止すること"""
        mock_validate.return_value = False
        mock_response_function = Mock()
        
        event_body = json.dumps({'events': []})
        
        line_handler.handle_line_event(event_body, "invalid_signature", mock_response_function)
        
        mock_validate.assert_called_once()
        mock_response_function.assert_not_called()
    
    def test_handle_line_event_no_channel_secret(self, monkeypatch):
        """チャンネルシークレットが設定されていない場合"""
        monkeypatch.delenv('LINE_CHANNEL_SECRET', raising=False)
        mock_response_function = Mock()
        
        event_body = json.dumps({'events': []})
        
        line_handler.handle_line_event(event_body, "test_signature", mock_response_function)
        
        mock_response_function.assert_not_called()
    
    @patch('app.line_handler.reply_message')
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_non_text_message(self, mock_validate, mock_reply, mock_environment_variables):
        """テキストメッセージ以外の場合は処理されないこと"""
        mock_validate.return_value = True
        mock_response_function = Mock()
        
        event_body = json.dumps({
            'events': [
                {
                    'type': 'message',
                    'replyToken': 'test_reply_token',
                    'source': {
                        'userId': 'test_user_id'
                    },
                    'message': {
                        'type': 'image',
                        'id': 'test_image_id'
                    }
                }
            ]
        })
        
        line_handler.handle_line_event(event_body, "test_signature", mock_response_function)
        
        mock_validate.assert_called_once()
        mock_response_function.assert_not_called()
        mock_reply.assert_not_called()
    
    @patch('app.line_handler.reply_message')
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_unfollow_event(self, mock_validate, mock_reply, mock_environment_variables):
        """アンフォローイベントが正しく処理されること"""
        mock_validate.return_value = True
        mock_response_function = Mock()
        
        event_body = json.dumps({
            'events': [
                {
                    'type': 'unfollow',
                    'source': {
                        'userId': 'test_user_id'
                    }
                }
            ]
        })
        
        line_handler.handle_line_event(event_body, "test_signature", mock_response_function)
        
        mock_validate.assert_called_once()
        mock_response_function.assert_called_once_with("test_user_id", "unfollow")
        mock_reply.assert_not_called()  # unfollowイベントでは返信しない
    
    @patch('app.line_handler.reply_message')
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_follow_event(self, mock_validate, mock_reply, mock_environment_variables):
        """フォローイベントなどその他のイベントは処理されないこと"""
        mock_validate.return_value = True
        mock_response_function = Mock()
        
        event_body = json.dumps({
            'events': [
                {
                    'type': 'follow',
                    'replyToken': 'test_reply_token',
                    'source': {
                        'userId': 'test_user_id'
                    }
                }
            ]
        })
        
        line_handler.handle_line_event(event_body, "test_signature", mock_response_function)
        
        mock_validate.assert_called_once()
        mock_response_function.assert_not_called()
        mock_reply.assert_not_called()