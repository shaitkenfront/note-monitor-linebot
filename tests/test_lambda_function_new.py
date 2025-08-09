import pytest
import json
from unittest.mock import patch, Mock
import lambda_function


class TestHandleUserMessage:
    """handle_user_message関数のテスト"""
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    def test_handle_user_message_valid_username(self, mock_db_handler):
        """有効なnote.comユーザー名を処理できること"""
        mock_db_instance = Mock()
        mock_db_handler.return_value = mock_db_instance
        mock_db_instance.count_user_mappings.return_value = 0
        mock_db_instance.get_user_mappings.return_value = []
        mock_db_instance.save_user_mapping.return_value = True
        
        result = lambda_function.handle_user_message('user123', 'test_user')
        
        assert '✅ note.comのユーザー名「test_user」を登録しました' in result
        assert '定期的にフォロワー数の通知を送信します' in result
        mock_db_instance.save_user_mapping.assert_called_once_with('user123', 'test_user')
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    def test_handle_user_message_save_failure(self, mock_db_handler):
        """DynamoDBへの保存に失敗した場合のエラーメッセージ"""
        mock_db_instance = Mock()
        mock_db_handler.return_value = mock_db_instance
        mock_db_instance.count_user_mappings.return_value = 0
        mock_db_instance.get_user_mappings.return_value = []
        mock_db_instance.save_user_mapping.return_value = False
        
        result = lambda_function.handle_user_message('user123', 'test_user')
        
        assert '❌ 登録に失敗しました' in result
        assert 'しばらく経ってから再度お試しください' in result
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    def test_handle_user_message_unfollow(self, mock_db_handler):
        """アンフォローイベントを処理できること"""
        mock_db_instance = Mock()
        mock_db_handler.return_value = mock_db_instance
        mock_db_instance.delete_user_mapping.return_value = True
        
        result = lambda_function.handle_user_message('user123', 'unfollow')
        
        assert result == 'User unregistered'
        mock_db_instance.delete_user_mapping.assert_called_once_with('user123')
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    def test_handle_user_message_invalid_username_with_existing_user(self, mock_db_handler):
        """無効なユーザー名の場合、既存のユーザー情報を表示すること"""
        mock_db_instance = Mock()
        mock_db_handler.return_value = mock_db_instance
        mock_db_instance.get_user_mappings.return_value = ['existing_user']
        
        result = lambda_function.handle_user_message('user123', 'xx')
        
        assert '📊 現在の登録情報' in result
        assert '• existing_user' in result
        assert '新しいユーザー名を登録する場合は' in result
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    def test_handle_user_message_invalid_username_new_user(self, mock_db_handler):
        """無効なユーザー名で新規ユーザーの場合、登録案内を表示すること"""
        mock_db_instance = Mock()
        mock_db_handler.return_value = mock_db_instance
        mock_db_instance.get_user_mappings.return_value = []
        
        result = lambda_function.handle_user_message('user123', 'xx')
        
        assert '📝 note.comのユーザー名を登録してください' in result
        assert '例：hekisaya' in result
        assert '3-16文字の英数字とアンダースコアのみ使用可能' in result
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    def test_handle_user_message_empty_message(self, mock_db_handler):
        """空メッセージの場合、登録案内を表示すること"""
        mock_db_instance = Mock()
        mock_db_handler.return_value = mock_db_instance
        mock_db_instance.get_user_mappings.return_value = []
        
        result = lambda_function.handle_user_message('user123', '')
        
        assert '📝 note.comのユーザー名を登録してください' in result
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    def test_handle_user_message_boundary_username(self, mock_db_handler):
        """境界値のユーザー名を正しく処理できること"""
        mock_db_instance = Mock()
        mock_db_handler.return_value = mock_db_instance
        mock_db_instance.count_user_mappings.return_value = 0
        mock_db_instance.get_user_mappings.return_value = []
        mock_db_instance.save_user_mapping.return_value = True
        
        # 3文字（最小）
        result = lambda_function.handle_user_message('user123', 'abc')
        assert '✅ note.comのユーザー名「abc」を登録しました' in result
        
        # 16文字（最大）
        result = lambda_function.handle_user_message('user123', 'abcdefghijklmnop')
        assert '✅ note.comのユーザー名「abcdefghijklmnop」を登録しました' in result


class TestGetNoteResponseForUser:
    """get_note_dashboard_response_for_user関数のテスト"""
    
    @patch('lambda_function.note_scraper.get_note_dashboard_response_for_user')
    def test_get_note_dashboard_response_for_user(self, mock_get_response):
        """指定ユーザーの情報取得が正しく動作すること"""
        mock_get_response.return_value = "test response for user"
        
        result = lambda_function.get_note_dashboard_response_for_user('test_user')
        
        assert result == "test response for user"
        mock_get_response.assert_called_once_with('test_user')


class TestIntegrationWithNewFeatures:
    """新機能の統合テスト"""
    
    @patch('lambda_function.line_handler.send_push_message')
    @patch('lambda_function.note_scraper.get_note_dashboard_response_for_user')
    @patch('lambda_function.db_handler.DynamoDBHandler')
    def test_scheduled_execution_multiple_users(self, mock_db_handler, mock_get_response, mock_send_push, sample_lambda_context):
        """複数ユーザーへのスケジュール実行が正しく動作すること"""
        # 複数ユーザーのモックデータ
        mock_db_instance = Mock()
        mock_db_handler.return_value = mock_db_instance
        mock_db_instance.get_all_user_mappings.return_value = [
            {'line_user_id': 'user1', 'note_username': 'note_user1'},
            {'line_user_id': 'user2', 'note_username': 'note_user2'},
            {'line_user_id': 'user3', 'note_username': 'note_user3'}
        ]
        
        # 各ユーザーに対して異なるレスポンスを設定
        mock_get_response.side_effect = [
            "Response for user1",
            "Response for user2", 
            "Response for user3"
        ]
        
        scheduled_event = {
            'source': 'aws.events',
            'detail-type': 'Scheduled Event'
        }
        
        result = lambda_function.lambda_handler(scheduled_event, sample_lambda_context)
        
        assert result['statusCode'] == 200
        assert 'Scheduled execution completed for 3 users' in result['body']
        
        # 各ユーザーに対して処理が実行されたことを確認
        assert mock_get_response.call_count == 3
        assert mock_send_push.call_count == 3
        
        # 各呼び出しの引数を確認
        mock_get_response.assert_any_call('note_user1')
        mock_get_response.assert_any_call('note_user2')
        mock_get_response.assert_any_call('note_user3')
        
        mock_send_push.assert_any_call('user1', 'Response for user1')
        mock_send_push.assert_any_call('user2', 'Response for user2')
        mock_send_push.assert_any_call('user3', 'Response for user3')
    
    @patch('lambda_function.line_handler.handle_line_event')
    def test_line_webhook_with_unfollow_event(self, mock_handle_event, sample_lambda_context):
        """アンフォローイベントを含むWebhookが正しく処理されること"""
        unfollow_event = {
            'headers': {
                'x-line-signature': 'test_signature'
            },
            'body': json.dumps({
                'events': [
                    {
                        'type': 'unfollow',
                        'source': {
                            'userId': 'user123'
                        }
                    }
                ]
            })
        }
        
        result = lambda_function.lambda_handler(unfollow_event, sample_lambda_context)
        
        assert result['statusCode'] == 200
        mock_handle_event.assert_called_once()
        
        # handle_user_message関数が渡されていることを確認
        args, kwargs = mock_handle_event.call_args
        response_function = args[2]
        assert response_function.__name__ == 'handle_user_message'
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    def test_user_registration_workflow(self, mock_db_handler):
        """ユーザー登録のワークフローが正しく動作すること"""
        mock_db_instance = Mock()
        mock_db_handler.return_value = mock_db_instance
        mock_db_instance.count_user_mappings.return_value = 0
        mock_db_instance.get_user_mappings.return_value = []
        mock_db_instance.save_user_mapping.return_value = True
        
        # 最初は未登録状態
        result = lambda_function.handle_user_message('user123', 'xx')  # 2文字なので無効
        assert '📝 note.comのユーザー名を登録してください' in result
        
        # 有効なユーザー名で登録
        result = lambda_function.handle_user_message('user123', 'valid_user')
        assert '✅ note.comのユーザー名「valid_user」を登録しました' in result
        
        # 登録後の状態確認
        mock_db_instance.get_user_mappings.return_value = ['valid_user']
        result = lambda_function.handle_user_message('user123', 'x@')  # 無効な文字を含む
        assert '📊 現在の登録情報' in result
        assert '• valid_user' in result