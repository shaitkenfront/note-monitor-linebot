import pytest
import boto3
from unittest.mock import patch, Mock
from moto import mock_aws
from app.db_handler import DynamoDBHandler


@mock_aws
class TestDynamoDBHandler:
    
    def setup_method(self, method):
        """テスト前の準備"""
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table_name = 'test-note-monitor-users'
        
        # テスト用のテーブルを作成（複合キー対応）
        self.table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {
                    'AttributeName': 'line_user_id',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'note_username',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'line_user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'note_username',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # テーブルが作成されるまで待機
        self.table.wait_until_exists()
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_save_user_mapping_success(self, mock_resource):
        """ユーザーマッピングの保存が正常に動作すること"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        result = handler.save_user_mapping('user123', 'test_user')
        
        assert result is True
        
        # 保存されたデータを確認
        response = self.table.get_item(Key={'line_user_id': 'user123', 'note_username': 'test_user'})
        item = response['Item']
        assert item['line_user_id'] == 'user123'
        assert item['note_username'] == 'test_user'
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_save_user_mapping_update_existing(self, mock_resource):
        """既存のユーザーマッピングを更新できること"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        # 最初のマッピングを保存
        handler.save_user_mapping('user123', 'old_user')
        
        # 同じユーザーIDで新しいマッピングを保存
        result = handler.save_user_mapping('user123', 'new_user')
        
        assert result is True
        
        # 更新されたデータを確認（複数のマッピングが存在する）
        mappings = handler.get_user_mappings('user123')
        assert len(mappings) == 2
        assert 'old_user' in mappings
        assert 'new_user' in mappings
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_delete_user_mapping_success(self, mock_resource):
        """ユーザーマッピングの削除が正常に動作すること"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        # まずデータを保存
        handler.save_user_mapping('user123', 'test_user')
        
        # 削除を実行
        result = handler.delete_user_mapping('user123')
        
        assert result is True
        
        # 削除されたことを確認
        mappings = handler.get_user_mappings('user123')
        assert len(mappings) == 0
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_delete_user_mapping_nonexistent(self, mock_resource):
        """存在しないユーザーマッピングの削除も正常に動作すること"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        result = handler.delete_user_mapping('nonexistent_user')
        
        assert result is True
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_get_user_mapping_success(self, mock_resource):
        """ユーザーマッピングの取得が正常に動作すること"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        # データを保存
        handler.save_user_mapping('user123', 'test_user')
        
        # 取得を実行
        result = handler.get_user_mapping('user123')
        
        assert result == 'test_user'
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_get_user_mapping_nonexistent(self, mock_resource):
        """存在しないユーザーマッピングの取得はNoneを返すこと"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        result = handler.get_user_mapping('nonexistent_user')
        
        assert result is None
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_get_all_user_mappings_success(self, mock_resource):
        """すべてのユーザーマッピングの取得が正常に動作すること"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        # 複数のデータを保存
        handler.save_user_mapping('user1', 'note_user1')
        handler.save_user_mapping('user2', 'note_user2')
        handler.save_user_mapping('user3', 'note_user3')
        
        # 全データを取得
        result = handler.get_all_user_mappings()
        
        assert len(result) == 3
        
        # ユーザーIDでソートして確認
        result_sorted = sorted(result, key=lambda x: x['line_user_id'])
        assert result_sorted[0]['line_user_id'] == 'user1'
        assert result_sorted[0]['note_username'] == 'note_user1'
        assert result_sorted[1]['line_user_id'] == 'user2'
        assert result_sorted[1]['note_username'] == 'note_user2'
        assert result_sorted[2]['line_user_id'] == 'user3'
        assert result_sorted[2]['note_username'] == 'note_user3'
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_get_all_user_mappings_empty(self, mock_resource):
        """データが存在しない場合は空のリストを返すこと"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        result = handler.get_all_user_mappings()
        
        assert result == []
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_get_all_line_user_ids_success(self, mock_resource):
        """すべてのLINEユーザーIDの取得が正常に動作すること"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        # 複数のデータを保存
        handler.save_user_mapping('user1', 'note_user1')
        handler.save_user_mapping('user2', 'note_user2')
        handler.save_user_mapping('user3', 'note_user3')
        
        # 全ユーザーIDを取得
        result = handler.get_all_line_user_ids()
        
        assert len(result) == 3
        assert set(result) == {'user1', 'user2', 'user3'}
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_get_all_line_user_ids_empty(self, mock_resource):
        """データが存在しない場合は空のリストを返すこと"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        result = handler.get_all_line_user_ids()
        
        assert result == []
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_default_table_name(self, mock_resource):
        """デフォルトのテーブル名が正しく設定されること"""
        mock_resource.return_value = self.dynamodb
        # 環境変数を削除
        with patch.dict('os.environ', {}, clear=True):
            handler = DynamoDBHandler()
            assert handler.table_name == 'note-monitor-users'
    
    @patch('app.db_handler.boto3.resource')
    def test_save_user_mapping_client_error(self, mock_resource):
        """DynamoDB ClientErrorが発生した場合はFalseを返すこと"""
        from botocore.exceptions import ClientError
        
        mock_table = Mock()
        mock_table.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Test error'}},
            'put_item'
        )
        mock_resource.return_value.Table.return_value = mock_table
        
        handler = DynamoDBHandler()
        result = handler.save_user_mapping('user123', 'test_user')
        
        assert result is False
    
    @patch('app.db_handler.boto3.resource')
    def test_delete_user_mapping_client_error(self, mock_resource):
        """DynamoDB ClientErrorが発生した場合はFalseを返すこと"""
        from botocore.exceptions import ClientError
        
        mock_table = Mock()
        mock_table.delete_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Test error'}},
            'delete_item'
        )
        mock_resource.return_value.Table.return_value = mock_table
        
        handler = DynamoDBHandler()
        result = handler.delete_user_mapping('user123')
        
        assert result is False
    
    @patch('app.db_handler.boto3.resource')
    def test_get_user_mapping_client_error(self, mock_resource):
        """DynamoDB ClientErrorが発生した場合はNoneを返すこと"""
        from botocore.exceptions import ClientError
        
        mock_table = Mock()
        mock_table.get_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Test error'}},
            'get_item'
        )
        mock_resource.return_value.Table.return_value = mock_table
        
        handler = DynamoDBHandler()
        result = handler.get_user_mapping('user123')
        
        assert result is None
    
    @patch('app.db_handler.boto3.resource')
    def test_get_all_user_mappings_client_error(self, mock_resource):
        """DynamoDB ClientErrorが発生した場合は空のリストを返すこと"""
        from botocore.exceptions import ClientError
        
        mock_table = Mock()
        mock_table.scan.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Test error'}},
            'scan'
        )
        mock_resource.return_value.Table.return_value = mock_table
        
        handler = DynamoDBHandler()
        result = handler.get_all_user_mappings()
        
        assert result == []
    
    @patch('app.db_handler.boto3.resource')
    def test_get_all_line_user_ids_client_error(self, mock_resource):
        """DynamoDB ClientErrorが発生した場合は空のリストを返すこと"""
        from botocore.exceptions import ClientError
        
        mock_table = Mock()
        mock_table.scan.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Test error'}},
            'scan'
        )
        mock_resource.return_value.Table.return_value = mock_table
        
        handler = DynamoDBHandler()
        result = handler.get_all_line_user_ids()
        
        assert result == []
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_count_user_mappings_success(self, mock_resource):
        """ユーザーマッピングの数をカウントできること"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        # 3つのマッピングを保存
        handler.save_user_mapping('user123', 'note_user1')
        handler.save_user_mapping('user123', 'note_user2')
        handler.save_user_mapping('user123', 'note_user3')
        
        # カウントを確認
        count = handler.count_user_mappings('user123')
        assert count == 3
        
        # 存在しないユーザー
        count = handler.count_user_mappings('nonexistent_user')
        assert count == 0
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_get_user_mappings_success(self, mock_resource):
        """複数のユーザーマッピングを取得できること"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        # 3つのマッピングを保存
        handler.save_user_mapping('user123', 'note_user1')
        handler.save_user_mapping('user123', 'note_user2')
        handler.save_user_mapping('user123', 'note_user3')
        
        # 全てのマッピングを取得
        mappings = handler.get_user_mappings('user123')
        assert len(mappings) == 3
        assert 'note_user1' in mappings
        assert 'note_user2' in mappings
        assert 'note_user3' in mappings
        
        # 存在しないユーザー
        mappings = handler.get_user_mappings('nonexistent_user')
        assert mappings == []
    
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'test-note-monitor-users'})
    @patch('app.db_handler.boto3.resource')
    def test_delete_user_mapping_with_username(self, mock_resource):
        """特定のnote.comユーザー名のマッピングを削除できること"""
        mock_resource.return_value = self.dynamodb
        handler = DynamoDBHandler()
        
        # 3つのマッピングを保存
        handler.save_user_mapping('user123', 'note_user1')
        handler.save_user_mapping('user123', 'note_user2')
        handler.save_user_mapping('user123', 'note_user3')
        
        # 特定のマッピングを削除
        result = handler.delete_user_mapping('user123', 'note_user2')
        assert result is True
        
        # 残りのマッピングを確認
        mappings = handler.get_user_mappings('user123')
        assert len(mappings) == 2
        assert 'note_user1' in mappings
        assert 'note_user3' in mappings
        assert 'note_user2' not in mappings