import pytest
import json
from unittest.mock import patch, Mock
from app import line_handler


class TestLineHandlerNewFeatures:
    """line_handlerの新機能のテスト"""
    
    @patch('app.line_handler.reply_message')
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_multiple_events(self, mock_validate, mock_reply, mock_environment_variables):
        """複数のイベントを含むWebhookが正しく処理されること"""
        mock_validate.return_value = True
        mock_response_function = Mock(return_value="response message")
        
        event_body = json.dumps({
            'events': [
                {
                    'type': 'message',
                    'replyToken': 'test_reply_token1',
                    'source': {
                        'userId': 'test_user_id1'
                    },
                    'message': {
                        'type': 'text',
                        'text': 'test message 1'
                    }
                },
                {
                    'type': 'message',
                    'replyToken': 'test_reply_token2',
                    'source': {
                        'userId': 'test_user_id2'
                    },
                    'message': {
                        'type': 'text',
                        'text': 'test message 2'
                    }
                }
            ]
        })
        
        line_handler.handle_line_event(event_body, "test_signature", mock_response_function)
        
        mock_validate.assert_called_once_with(event_body, "test_signature", "test_channel_secret")
        assert mock_response_function.call_count == 2
        assert mock_reply.call_count == 2
        
        # 各イベントの処理を確認
        mock_response_function.assert_any_call("test_user_id1", "test message 1")
        mock_response_function.assert_any_call("test_user_id2", "test message 2")
        mock_reply.assert_any_call("test_reply_token1", "response message")
        mock_reply.assert_any_call("test_reply_token2", "response message")
    
    @patch('app.line_handler.reply_message')
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_mixed_events(self, mock_validate, mock_reply, mock_environment_variables):
        """メッセージとアンフォローイベントが混在する場合の処理"""
        mock_validate.return_value = True
        mock_response_function = Mock(return_value="response message")
        
        event_body = json.dumps({
            'events': [
                {
                    'type': 'message',
                    'replyToken': 'test_reply_token',
                    'source': {
                        'userId': 'test_user_id1'
                    },
                    'message': {
                        'type': 'text',
                        'text': 'test message'
                    }
                },
                {
                    'type': 'unfollow',
                    'source': {
                        'userId': 'test_user_id2'
                    }
                }
            ]
        })
        
        line_handler.handle_line_event(event_body, "test_signature", mock_response_function)
        
        mock_validate.assert_called_once()
        assert mock_response_function.call_count == 2
        mock_reply.assert_called_once()  # メッセージイベントのみ返信
        
        # 各イベントの処理を確認
        mock_response_function.assert_any_call("test_user_id1", "test message")
        mock_response_function.assert_any_call("test_user_id2", "unfollow")
        mock_reply.assert_called_once_with("test_reply_token", "response message")
    
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_user_id_extraction(self, mock_validate, mock_environment_variables):
        """ユーザーIDが正しく抽出されること"""
        mock_validate.return_value = True
        mock_response_function = Mock(return_value="response message")
        
        event_body = json.dumps({
            'events': [
                {
                    'type': 'message',
                    'replyToken': 'test_reply_token',
                    'source': {
                        'userId': 'U1234567890abcdef'
                    },
                    'message': {
                        'type': 'text',
                        'text': 'test message'
                    }
                }
            ]
        })
        
        line_handler.handle_line_event(event_body, "test_signature", mock_response_function)
        
        # 正しいユーザーIDが渡されることを確認
        mock_response_function.assert_called_once_with("U1234567890abcdef", "test message")
    
    @patch('app.line_handler.reply_message')
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_empty_events(self, mock_validate, mock_reply, mock_environment_variables):
        """空のイベントリストが正しく処理されること"""
        mock_validate.return_value = True
        mock_response_function = Mock()
        
        event_body = json.dumps({
            'events': []
        })
        
        line_handler.handle_line_event(event_body, "test_signature", mock_response_function)
        
        mock_validate.assert_called_once()
        mock_response_function.assert_not_called()
        mock_reply.assert_not_called()
    
    @patch('app.line_handler.reply_message')
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_response_function_error(self, mock_validate, mock_reply, mock_environment_variables):
        """response_functionでエラーが発生した場合の処理"""
        mock_validate.return_value = True
        mock_response_function = Mock(side_effect=Exception("Test error"))
        
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
        
        # エラーが発生しても例外が発生しないことを確認
        line_handler.handle_line_event(event_body, "test_signature", mock_response_function)
        
        mock_validate.assert_called_once()
        mock_response_function.assert_called_once_with("test_user_id", "test message")
        # エラーが発生した場合は返信しない
        mock_reply.assert_not_called()
    
    @patch('app.line_handler.reply_message')
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_different_message_types(self, mock_validate, mock_reply, mock_environment_variables):
        """様々なメッセージタイプの処理"""
        mock_validate.return_value = True
        mock_response_function = Mock(return_value="response message")
        
        event_body = json.dumps({
            'events': [
                {
                    'type': 'message',
                    'replyToken': 'test_reply_token1',
                    'source': {
                        'userId': 'test_user_id1'
                    },
                    'message': {
                        'type': 'text',
                        'text': 'text message'
                    }
                },
                {
                    'type': 'message',
                    'replyToken': 'test_reply_token2',
                    'source': {
                        'userId': 'test_user_id2'
                    },
                    'message': {
                        'type': 'sticker',
                        'id': 'test_sticker_id'
                    }
                },
                {
                    'type': 'message',
                    'replyToken': 'test_reply_token3',
                    'source': {
                        'userId': 'test_user_id3'
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
        # テキストメッセージのみ処理される
        mock_response_function.assert_called_once_with("test_user_id1", "text message")
        mock_reply.assert_called_once_with("test_reply_token1", "response message")
    
    @patch('app.line_handler.reply_message')
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_group_chat(self, mock_validate, mock_reply, mock_environment_variables):
        """グループチャットからのイベント処理"""
        mock_validate.return_value = True
        mock_response_function = Mock(return_value="response message")
        
        event_body = json.dumps({
            'events': [
                {
                    'type': 'message',
                    'replyToken': 'test_reply_token',
                    'source': {
                        'type': 'group',
                        'groupId': 'C1234567890abcdef',
                        'userId': 'U1234567890abcdef'
                    },
                    'message': {
                        'type': 'text',
                        'text': 'group message'
                    }
                }
            ]
        })
        
        line_handler.handle_line_event(event_body, "test_signature", mock_response_function)
        
        mock_validate.assert_called_once()
        # グループチャットでもユーザーIDが正しく抽出される
        mock_response_function.assert_called_once_with("U1234567890abcdef", "group message")
        mock_reply.assert_called_once_with("test_reply_token", "response message")
    
    @patch('app.line_handler.reply_message')
    @patch('app.line_handler.validate_signature')
    def test_handle_line_event_malformed_json(self, mock_validate, mock_reply, mock_environment_variables):
        """不正なJSON形式のイベントボディの処理"""
        mock_validate.return_value = True
        mock_response_function = Mock()
        
        # 不正なJSON
        event_body = "{'events': [invalid json"
        
        # JSONパースエラーが発生しても例外が発生しないことを確認
        line_handler.handle_line_event(event_body, "test_signature", mock_response_function)
        
        mock_validate.assert_called_once()
        mock_response_function.assert_not_called()
        mock_reply.assert_not_called()