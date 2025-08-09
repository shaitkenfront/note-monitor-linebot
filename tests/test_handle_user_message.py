import pytest
from unittest.mock import patch, Mock
from lambda_function import handle_user_message


class TestHandleUserMessage:
    """handle_user_message関数のテスト - t_wada流テスト設計に基づく"""

    class TestUnfollowEvent:
        """アンフォローイベントのテスト"""

        @patch('lambda_function.db_handler.DynamoDBHandler')
        def test_unfollowメッセージを受信した場合_ユーザーマッピングが削除される(self, mock_db_handler):
            # Given: アンフォローイベント
            mock_db = Mock()
            mock_db_handler.return_value = mock_db
            user_id = "test_user_123"
            message = "unfollow"
            
            # When: アンフォローメッセージを処理
            result = handle_user_message(user_id, message)
            
            # Then: ユーザーマッピングが削除され、適切なメッセージが返される
            mock_db.delete_user_mapping.assert_called_once_with(user_id)
            assert result == "User unregistered"


    class TestValidNoteUsernameRegistration:
        """有効なnote.comユーザー名の登録テスト"""

        @patch('lambda_function.db_handler.DynamoDBHandler')
        @patch('lambda_function.validator.validate_note_username')
        def test_初回登録で有効なユーザー名の場合_DBに保存され成功メッセージが返される(self, mock_validate, mock_db_handler):
            # Given: 初回登録で有効なユーザー名
            mock_validate.return_value = True
            mock_db = Mock()
            mock_db.count_user_mappings.return_value = 0  # 未登録
            mock_db.get_user_mappings.return_value = []
            mock_db.save_user_mapping.return_value = True  # 保存成功
            mock_db_handler.return_value = mock_db
            
            user_id = "user_001"
            username = "valid_user"
            
            # When: 有効なユーザー名で登録を試行
            result = handle_user_message(user_id, username)
            
            # Then: DBに保存され、成功メッセージが返される
            mock_db.save_user_mapping.assert_called_once_with(user_id, username)
            expected_message = "✅ note.comのユーザー名「valid_user」を登録しました。\n定期的にフォロワー数の通知を送信します。"
            assert result == expected_message

        @patch('lambda_function.db_handler.DynamoDBHandler')
        @patch('lambda_function.validator.validate_note_username')
        def test_初回登録で保存に失敗した場合_エラーメッセージが返される(self, mock_validate, mock_db_handler):
            # Given: 初回登録だがDB保存に失敗
            mock_validate.return_value = True
            mock_db = Mock()
            mock_db.count_user_mappings.return_value = 0
            mock_db.get_user_mappings.return_value = []
            mock_db.save_user_mapping.return_value = False  # 保存失敗
            mock_db_handler.return_value = mock_db
            
            user_id = "user_002"
            username = "valid_user"
            
            # When: DB保存に失敗
            result = handle_user_message(user_id, username)
            
            # Then: エラーメッセージが返される
            expected_message = "❌ 登録に失敗しました。しばらく経ってから再度お試しください。"
            assert result == expected_message


    class TestDuplicateRegistration:
        """重複登録のテスト"""

        @patch('lambda_function.db_handler.DynamoDBHandler')
        @patch('lambda_function.validator.validate_note_username')
        def test_既に登録済みの同じユーザー名の場合_警告メッセージが返される(self, mock_validate, mock_db_handler):
            # Given: 既に登録済みの同じユーザー名
            mock_validate.return_value = True
            mock_db = Mock()
            mock_db.count_user_mappings.return_value = 1
            mock_db.get_user_mappings.return_value = ['existing_user']
            mock_db_handler.return_value = mock_db
            
            user_id = "user_003"
            username = "existing_user"  # 既に登録済み
            
            # When: 既に登録済みのユーザー名で登録を試行
            result = handle_user_message(user_id, username)
            
            # Then: 警告メッセージが返され、DBには保存されない
            mock_db.save_user_mapping.assert_not_called()
            expected_message = "⚠️ 「existing_user」は既に登録されています。"
            assert result == expected_message


    class TestOnDemandFetch:
        """オンデマンド取得のテスト"""

        @patch('lambda_function.db_handler.DynamoDBHandler')
        @patch('lambda_function.validator.validate_note_username')
        @patch('lambda_function.get_note_dashboard_response_for_user')
        def test_登録数制限に達している状態で有効なユーザー名の場合_オンデマンドでフォロワー数が取得される(
            self, mock_get_response, mock_validate, mock_db_handler
        ):
            # Given: 登録数制限(1個)に達している状態
            mock_validate.return_value = True
            mock_db = Mock()
            mock_db.count_user_mappings.return_value = 1  # 制限に達している
            mock_db.get_user_mappings.return_value = ['registered_user']
            mock_db_handler.return_value = mock_db
            mock_get_response.return_value = "👤 アカウント: other_user\n👥 フォロワー数: 1,234人"
            
            user_id = "user_004"
            username = "other_user"  # 登録済みとは異なるユーザー名
            
            # When: 制限に達している状態で別のユーザー名を送信
            result = handle_user_message(user_id, username)
            
            # Then: オンデマンド取得が実行され、フォロワー数情報が返される
            mock_get_response.assert_called_once_with(username)
            mock_db.save_user_mapping.assert_not_called()  # DBには保存されない
            expected_message = "📊 現在のフォロワー数情報\n\n👤 アカウント: other_user\n👥 フォロワー数: 1,234人"
            assert result == expected_message

        @patch('lambda_function.db_handler.DynamoDBHandler')
        @patch('lambda_function.validator.validate_note_username')
        @patch('lambda_function.get_note_dashboard_response_for_user')
        def test_オンデマンド取得でエラーが発生した場合_エラー情報が含まれたメッセージが返される(
            self, mock_get_response, mock_validate, mock_db_handler
        ):
            # Given: 登録数制限に達している状態でスクレイピングエラー
            mock_validate.return_value = True
            mock_db = Mock()
            mock_db.count_user_mappings.return_value = 1
            mock_db.get_user_mappings.return_value = ['registered_user']
            mock_db_handler.return_value = mock_db
            mock_get_response.return_value = "❌ エラー: フォロワー数の情報が見つかりません。URLが正しいか確認してください。"
            
            user_id = "user_005"
            username = "error_user"
            
            # When: エラーが発生するユーザー名でオンデマンド取得
            result = handle_user_message(user_id, username)
            
            # Then: エラー情報が含まれたメッセージが返される
            mock_get_response.assert_called_once_with(username)
            expected_message = "📊 現在のフォロワー数情報\n\n❌ エラー: フォロワー数の情報が見つかりません。URLが正しいか確認してください。"
            assert result == expected_message


    class TestInvalidUsername:
        """無効なユーザー名のテスト"""

        @patch('lambda_function.db_handler.DynamoDBHandler')
        @patch('lambda_function.validator.validate_note_username')
        def test_無効なユーザー名で登録情報がある場合_現在の登録情報が表示される(self, mock_validate, mock_db_handler):
            # Given: 無効なユーザー名で既存の登録情報がある
            mock_validate.return_value = False  # 無効なユーザー名
            mock_db = Mock()
            mock_db.get_user_mappings.return_value = ['registered_user']
            mock_db_handler.return_value = mock_db
            
            user_id = "user_006"
            invalid_message = "x@"  # 無効な文字を含む
            
            # When: 無効なメッセージを送信
            result = handle_user_message(user_id, invalid_message)
            
            # Then: 現在の登録情報が表示される
            expected_message = (
                "📊 現在の登録情報 (1/1)\n\n"
                "👤 note.comユーザー名:\n• registered_user\n\n"
                "新しいユーザー名を登録する場合は、既存の登録を削除してから3-16文字の英数字とアンダースコアで入力してください。"
            )
            assert result == expected_message

        @patch('lambda_function.db_handler.DynamoDBHandler')
        @patch('lambda_function.validator.validate_note_username')
        def test_無効なユーザー名で登録情報がない場合_登録案内メッセージが表示される(self, mock_validate, mock_db_handler):
            # Given: 無効なユーザー名で登録情報がない
            mock_validate.return_value = False
            mock_db = Mock()
            mock_db.get_user_mappings.return_value = []  # 登録情報なし
            mock_db_handler.return_value = mock_db
            
            user_id = "user_007"
            invalid_message = "xx"  # 短すぎる
            
            # When: 無効なメッセージを送信
            result = handle_user_message(user_id, invalid_message)
            
            # Then: 登録案内メッセージが表示される
            expected_message = (
                "📝 note.comのユーザー名を登録してください。\n\n"
                "例：hekisaya\n\n"
                "※ 3-16文字の英数字とアンダースコアのみ使用可能です。"
            )
            assert result == expected_message


    class TestBoundaryValues:
        """境界値テスト"""

        @patch('lambda_function.db_handler.DynamoDBHandler')
        @patch('lambda_function.validator.validate_note_username')
        def test_登録数がちょうど制限値の場合_オンデマンド取得が実行される(self, mock_validate, mock_db_handler):
            # Given: 登録数がちょうど制限値(1)
            mock_validate.return_value = True
            mock_db = Mock()
            mock_db.count_user_mappings.return_value = 1  # ちょうど制限値
            mock_db.get_user_mappings.return_value = ['user1']
            mock_db_handler.return_value = mock_db
            
            with patch('lambda_function.get_note_dashboard_response_for_user') as mock_get_response:
                mock_get_response.return_value = "dummy response"
                
                user_id = "boundary_user"
                username = "new_user"
                
                # When: 新しいユーザー名を送信
                result = handle_user_message(user_id, username)
                
                # Then: オンデマンド取得が実行される
                mock_get_response.assert_called_once_with(username)
                assert "📊 現在のフォロワー数情報" in result

        @patch('lambda_function.db_handler.DynamoDBHandler')
        @patch('lambda_function.validator.validate_note_username')
        def test_登録数が制限値未満の場合_通常の登録処理が実行される(self, mock_validate, mock_db_handler):
            # Given: 登録数が制限値未満(0)
            mock_validate.return_value = True
            mock_db = Mock()
            mock_db.count_user_mappings.return_value = 0  # 制限値未満
            mock_db.get_user_mappings.return_value = []
            mock_db.save_user_mapping.return_value = True
            mock_db_handler.return_value = mock_db
            
            user_id = "boundary_user2"
            username = "first_user"
            
            # When: 初回登録
            result = handle_user_message(user_id, username)
            
            # Then: 通常の登録処理が実行される
            mock_db.save_user_mapping.assert_called_once_with(user_id, username)
            assert "✅" in result and "登録しました" in result


    class TestUserIdEdgeCases:
        """ユーザーIDのエッジケース"""

        @patch('lambda_function.db_handler.DynamoDBHandler')
        @patch('lambda_function.validator.validate_note_username')
        def test_空のユーザーIDでも処理が正常に実行される(self, mock_validate, mock_db_handler):
            # Given: 空のユーザーID
            mock_validate.return_value = True
            mock_db = Mock()
            mock_db.count_user_mappings.return_value = 0
            mock_db.get_user_mappings.return_value = []
            mock_db.save_user_mapping.return_value = True
            mock_db_handler.return_value = mock_db
            
            user_id = ""  # 空のユーザーID
            username = "test_user"
            
            # When: 空のユーザーIDで処理
            result = handle_user_message(user_id, username)
            
            # Then: 正常に処理される（DB操作でエラーが出るかは別レイヤーの問題）
            mock_db.save_user_mapping.assert_called_once_with(user_id, username)