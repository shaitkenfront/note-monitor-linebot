import pytest
import json
from unittest.mock import patch, Mock
import lambda_function


class TestLambdaFunction:
    
    @patch('lambda_function.note_scraper.get_note_dashboard_response')
    def test_get_note_dashboard_response(self, mock_get_response):
        """get_note_dashboard_responseが正しく動作すること"""
        mock_get_response.return_value = "test response"
        
        result = lambda_function.get_note_dashboard_response()
        
        assert result == "test response"
        mock_get_response.assert_called_once()
    
    @patch('lambda_function.handle_scheduled_execution')
    def test_lambda_handler_scheduled_event(self, mock_handle_scheduled, sample_scheduled_event, sample_lambda_context):
        """スケジュールイベントの場合は適切な処理が呼び出されること"""
        mock_handle_scheduled.return_value = {'statusCode': 200, 'body': 'OK'}
        
        result = lambda_function.lambda_handler(sample_scheduled_event, sample_lambda_context)
        
        assert result['statusCode'] == 200
        mock_handle_scheduled.assert_called_once_with(sample_lambda_context)
    
    @patch('lambda_function.handle_line_webhook')
    def test_lambda_handler_line_webhook(self, mock_handle_webhook, sample_line_webhook_event, sample_lambda_context):
        """LINE Webhookイベントの場合は適切な処理が呼び出されること"""
        mock_handle_webhook.return_value = {'statusCode': 200, 'body': 'OK'}
        
        result = lambda_function.lambda_handler(sample_line_webhook_event, sample_lambda_context)
        
        assert result['statusCode'] == 200
        mock_handle_webhook.assert_called_once_with(sample_line_webhook_event, sample_lambda_context)
    
    def test_lambda_handler_invalid_event(self, sample_lambda_context):
        """無効なイベントの場合は400エラーを返すこと"""
        invalid_event = {'invalid': 'event'}
        
        result = lambda_function.lambda_handler(invalid_event, sample_lambda_context)
        
        assert result['statusCode'] == 400
        assert 'Invalid event type' in result['body']
    
    @patch('lambda_function.line_handler.send_push_message')
    @patch('lambda_function.db_handler.DynamoDBHandler')
    def test_handle_scheduled_execution_success(self, mock_db_handler, mock_send_push, sample_lambda_context):
        """スケジュール実行が正常に動作すること"""
        # DynamoDBのモックを設定
        mock_db_instance = Mock()
        mock_db_handler.return_value = mock_db_instance
        mock_db_instance.get_all_user_mappings.return_value = [
            {'line_user_id': 'user1', 'note_username': 'note_user1'},
            {'line_user_id': 'user2', 'note_username': 'note_user2'}
        ]
        
        # note_scraperのモックを設定
        with patch('lambda_function.get_note_dashboard_response_for_user') as mock_get_response:
            mock_get_response.return_value = "test dashboard info"
            
            result = lambda_function.handle_scheduled_execution(sample_lambda_context)
            
            assert result['statusCode'] == 200
            assert 'Scheduled execution completed for 2 users' in result['body']
            
            # 各ユーザーに対して処理が実行されたことを確認
            assert mock_get_response.call_count == 2
            assert mock_send_push.call_count == 2
            
            # 呼び出し引数を確認
            mock_get_response.assert_any_call('note_user1')
            mock_get_response.assert_any_call('note_user2')
            mock_send_push.assert_any_call('user1', 'test dashboard info')
            mock_send_push.assert_any_call('user2', 'test dashboard info')
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    def test_handle_scheduled_execution_no_users(self, mock_db_handler, sample_lambda_context):
        """登録ユーザーがいない場合は適切なメッセージを返すこと"""
        mock_db_instance = Mock()
        mock_db_handler.return_value = mock_db_instance
        mock_db_instance.get_all_user_mappings.return_value = []
        
        result = lambda_function.handle_scheduled_execution(sample_lambda_context)
        
        assert result['statusCode'] == 200
        assert 'No registered users found' in result['body']
    
    @patch('lambda_function.line_handler.handle_line_event')
    def test_handle_line_webhook_success(self, mock_handle_event, sample_line_webhook_event, sample_lambda_context):
        """LINE Webhook処理が正常に動作すること"""
        result = lambda_function.handle_line_webhook(sample_line_webhook_event, sample_lambda_context)
        
        assert result['statusCode'] == 200
        assert 'OK' in result['body']
        mock_handle_event.assert_called_once()
        
        # handle_line_eventの呼び出し引数を確認
        args, kwargs = mock_handle_event.call_args
        assert args[0] == sample_line_webhook_event['body']
        assert args[1] == sample_line_webhook_event['headers']['x-line-signature']
        # 3番目の引数は関数オブジェクト
        assert callable(args[2])
    
    def test_handle_line_webhook_missing_signature(self, sample_lambda_context):
        """署名が不足している場合は400エラーを返すこと"""
        event_without_signature = {
            'headers': {},
            'body': '{"events": []}'
        }
        
        result = lambda_function.handle_line_webhook(event_without_signature, sample_lambda_context)
        
        assert result['statusCode'] == 400
        assert 'Missing X-Line-Signature' in result['body']
    
    def test_handle_line_webhook_missing_body(self, sample_lambda_context):
        """ボディが不足している場合は400エラーを返すこと"""
        event_without_body = {
            'headers': {
                'x-line-signature': 'test_signature'
            }
        }
        
        result = lambda_function.handle_line_webhook(event_without_body, sample_lambda_context)
        
        assert result['statusCode'] == 400
        assert 'Missing body' in result['body']


class TestIntegration:
    """統合テスト"""
    
    @patch('lambda_function.line_handler.send_push_message')
    @patch('lambda_function.note_scraper.get_dashboard_info_from_note_url')
    @patch('lambda_function.db_handler.DynamoDBHandler')
    def test_end_to_end_scheduled_execution(self, mock_db_handler, mock_get_dashboard, mock_send_push, sample_lambda_context):
        """スケジュール実行の統合テスト"""
        # DynamoDBのモック設定
        mock_db_instance = Mock()
        mock_db_handler.return_value = mock_db_instance
        mock_db_instance.get_all_user_mappings.return_value = [
            {'line_user_id': 'user1', 'note_username': 'test_user'}
        ]
        
        mock_get_dashboard.return_value = {
            'followers_count': 1234,
            'url': 'https://note.com/test_user',
            'last_updated': '2023-01-01 12:00:00'
        }
        
        scheduled_event = {
            'source': 'aws.events',
            'detail-type': 'Scheduled Event'
        }
        
        result = lambda_function.lambda_handler(scheduled_event, sample_lambda_context)
        
        assert result['statusCode'] == 200
        mock_get_dashboard.assert_called_once_with('https://note.com/test_user')
        mock_send_push.assert_called_once()
        
        # 送信されたメッセージの内容を確認
        args, kwargs = mock_send_push.call_args
        assert args[0] == 'user1'
        assert '📊 note.com フォロワー数情報' in args[1]
        assert '1,234人' in args[1]
    
    @patch('lambda_function.line_handler.handle_line_event')
    def test_end_to_end_line_webhook(self, mock_handle_event, sample_lambda_context):
        """LINE Webhook処理の統合テスト"""
        line_webhook_event = {
            'headers': {
                'x-line-signature': 'test_signature'
            },
            'body': json.dumps({
                'events': [
                    {
                        'type': 'message',
                        'replyToken': 'test_reply_token',
                        'source': {
                            'userId': 'test_user_id'
                        },
                        'message': {
                            'type': 'text',
                            'text': 'test_username'
                        }
                    }
                ]
            })
        }
        
        result = lambda_function.lambda_handler(line_webhook_event, sample_lambda_context)
        
        assert result['statusCode'] == 200
        mock_handle_event.assert_called_once()
        
        # response_functionが正しく設定されているか確認
        args, kwargs = mock_handle_event.call_args
        response_function = args[2]
        
        # response_functionがhandle_user_messageであることを確認
        assert response_function.__name__ == 'handle_user_message'