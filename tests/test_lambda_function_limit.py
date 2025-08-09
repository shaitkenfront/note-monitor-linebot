import pytest
from unittest.mock import patch, Mock
from lambda_function import handle_user_message


class TestLambdaFunctionLimit:
    """Lambda関数の制限チェック機能のテスト"""
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    @patch('lambda_function.validator.validate_note_username')
    @patch('lambda_function.get_note_dashboard_response_for_user')
    def test_handle_user_message_limit_reached_ondemand_fetch(self, mock_get_response, mock_validate, mock_db_handler):
        """1個制限に達した場合、オンデマンドでフォロワー数を取得"""
        # モックの設定
        mock_validate.return_value = True
        mock_db = Mock()
        mock_db.count_user_mappings.return_value = 1
        mock_db.get_user_mappings.return_value = ['user1']
        mock_db_handler.return_value = mock_db
        mock_get_response.return_value = "👤 アカウント: new_user\n👥 フォロワー数: 5,678人"
        
        # テスト実行
        result = handle_user_message('test_user', 'new_user')
        
        # 期待される結果
        expected_result = "📊 現在のフォロワー数情報\n\n👤 アカウント: new_user\n👥 フォロワー数: 5,678人"
        assert result == expected_result
        mock_db.save_user_mapping.assert_not_called()
        mock_get_response.assert_called_once_with('new_user')
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    @patch('lambda_function.validator.validate_note_username')
    def test_handle_user_message_duplicate_username(self, mock_validate, mock_db_handler):
        """同じユーザー名を再登録しようとした場合のメッセージ処理"""
        # モックの設定
        mock_validate.return_value = True
        mock_db = Mock()
        mock_db.count_user_mappings.return_value = 1
        mock_db.get_user_mappings.return_value = ['user1']
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
        mock_db.count_user_mappings.return_value = 0
        mock_db.get_user_mappings.return_value = []
        mock_db.save_user_mapping.return_value = True
        mock_db_handler.return_value = mock_db
        
        # テスト実行
        result = handle_user_message('test_user', 'user1')
        
        # 期待される結果
        assert result == "✅ note.comのユーザー名「user1」を登録しました。\n定期的にフォロワー数の通知を送信します。"
        mock_db.save_user_mapping.assert_called_once_with('test_user', 'user1')
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    @patch('lambda_function.validator.validate_note_username')
    def test_handle_user_message_display_single_registration(self, mock_validate, mock_db_handler):
        """1つの登録情報を表示"""
        # モックの設定
        mock_validate.return_value = False  # 無効なユーザー名として扱う
        mock_db = Mock()
        mock_db.get_user_mappings.return_value = ['user1']
        mock_db_handler.return_value = mock_db
        
        # テスト実行
        result = handle_user_message('test_user', 'invalid_message')
        
        # 期待される結果
        expected_result = "📊 現在の登録情報 (1/1)\n\n👤 note.comユーザー名:\n• user1\n\n新しいユーザー名を登録する場合は、既存の登録を削除してから3-16文字の英数字とアンダースコアで入力してください。"
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
    
    @patch('lambda_function.db_handler.DynamoDBHandler')
    @patch('lambda_function.validator.validate_note_username')
    @patch('lambda_function.get_note_dashboard_response_for_user')
    def test_ondemand_fetch_with_error(self, mock_get_response, mock_validate, mock_db_handler):
        """制限時のオンデマンド取得でエラーが発生した場合の処理"""
        # モックの設定
        mock_validate.return_value = True
        mock_db = Mock()
        mock_db.count_user_mappings.return_value = 1
        mock_db.get_user_mappings.return_value = ['existing_user']  # 異なるユーザー名を返すことで制限に達している状況を作る
        mock_db_handler.return_value = mock_db
        mock_get_response.return_value = "❌ エラー: フォロワー数の情報が見つかりません。URLが正しいか確認してください。"
        
        # テスト実行
        result = handle_user_message('test_user', 'error_user')
        
        # 期待される結果
        expected_result = "📊 現在のフォロワー数情報\n\n❌ エラー: フォロワー数の情報が見つかりません。URLが正しいか確認してください。"
        assert result == expected_result
        mock_get_response.assert_called_once_with('error_user')