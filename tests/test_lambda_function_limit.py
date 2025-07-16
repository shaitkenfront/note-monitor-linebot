import pytest
from unittest.mock import patch, Mock
from lambda_function import handle_user_message


class TestLambdaFunctionLimit:
    """Lambda関数の制限チェック機能のテスト"""
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    @patch('lambda_function.validator.validate_note_username')
    def test_handle_user_message_limit_reached(self, mock_validate, mock_db_handler):
        """3個制限に達した場合のメッセージ処理"""
        # モックの設定
        mock_validate.return_value = True
        mock_db = Mock()
        mock_db.count_user_mappings.return_value = 3
        mock_db.get_user_mappings.return_value = ['user1', 'user2', 'user3']
        mock_db_handler.return_value = mock_db
        
        # テスト実行
        result = handle_user_message('test_user', 'new_user')
        
        # 期待される結果
        assert result == "⚠️ 登録できるnoteユーザーIDは3個までです。"
        mock_db.save_user_mapping.assert_not_called()
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    @patch('lambda_function.validator.validate_note_username')
    def test_handle_user_message_duplicate_username(self, mock_validate, mock_db_handler):
        """同じユーザー名を再登録しようとした場合のメッセージ処理"""
        # モックの設定
        mock_validate.return_value = True
        mock_db = Mock()
        mock_db.count_user_mappings.return_value = 2
        mock_db.get_user_mappings.return_value = ['user1', 'user2']
        mock_db_handler.return_value = mock_db
        
        # テスト実行
        result = handle_user_message('test_user', 'user1')
        
        # 期待される結果
        assert result == "⚠️ 「user1」は既に登録されています。"
        mock_db.save_user_mapping.assert_not_called()
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    @patch('lambda_function.validator.validate_note_username')
    def test_handle_user_message_successful_registration(self, mock_validate, mock_db_handler):
        """正常な登録処理"""
        # モックの設定
        mock_validate.return_value = True
        mock_db = Mock()
        mock_db.count_user_mappings.return_value = 2
        mock_db.get_user_mappings.return_value = ['user1', 'user2']
        mock_db.save_user_mapping.return_value = True
        mock_db_handler.return_value = mock_db
        
        # テスト実行
        result = handle_user_message('test_user', 'user3')
        
        # 期待される結果
        assert result == "✅ note.comのユーザー名「user3」を登録しました。\n定期的にフォロワー数の通知を送信します。"
        mock_db.save_user_mapping.assert_called_once_with('test_user', 'user3')
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    @patch('lambda_function.validator.validate_note_username')
    def test_handle_user_message_display_multiple_registrations(self, mock_validate, mock_db_handler):
        """複数の登録情報を表示"""
        # モックの設定
        mock_validate.return_value = False  # 無効なユーザー名として扱う
        mock_db = Mock()
        mock_db.get_user_mappings.return_value = ['user1', 'user2', 'user3']
        mock_db_handler.return_value = mock_db
        
        # テスト実行
        result = handle_user_message('test_user', 'invalid_message')
        
        # 期待される結果
        expected_result = "📊 現在の登録情報 (3/3)\n\n👤 note.comユーザー名:\n• user1\n• user2\n• user3\n\n新しいユーザー名を登録する場合は、3-16文字の英数字とアンダースコアで入力してください。"
        assert result == expected_result
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    @patch('lambda_function.validator.validate_note_username')
    def test_handle_user_message_display_no_registrations(self, mock_validate, mock_db_handler):
        """登録情報がない場合の表示"""
        # モックの設定
        mock_validate.return_value = False  # 無効なユーザー名として扱う
        mock_db = Mock()
        mock_db.get_user_mappings.return_value = []
        mock_db_handler.return_value = mock_db
        
        # テスト実行
        result = handle_user_message('test_user', 'invalid_message')
        
        # 期待される結果
        expected_result = "📝 note.comのユーザー名を登録してください。\n\n例：hekisaya\n\n※ 3-16文字の英数字とアンダースコアのみ使用可能です。"
        assert result == expected_result