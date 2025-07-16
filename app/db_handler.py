import boto3
import os
from typing import List, Dict, Optional
from botocore.exceptions import ClientError

class DynamoDBHandler:
    """
    DynamoDBでのユーザー情報管理を行うクラス
    """

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'note-monitor-users')
        self.table = self.dynamodb.Table(self.table_name)

    def save_user_mapping(self, line_user_id: str, note_username: str) -> bool:
        """
        LINE ユーザーIDと note.com ユーザー名のマッピングを保存
        """
        try:
            self.table.put_item(
                Item={
                    'line_user_id': line_user_id,
                    'note_username': note_username
                }
            )
            return True
        except ClientError as e:
            print(f"Error saving user mapping: {e}")
            return False

    def count_user_mappings(self, line_user_id: str) -> int:
        """
        指定されたLINEユーザーIDの登録数をカウント
        """
        try:
            response = self.table.query(
                KeyConditionExpression='line_user_id = :line_user_id',
                ExpressionAttributeValues={
                    ':line_user_id': line_user_id
                }
            )
            return len(response.get('Items', []))
        except ClientError as e:
            print(f"Error counting user mappings: {e}")
            return 0

    def delete_user_mapping(self, line_user_id: str, note_username: str = None) -> bool:
        """
        LINE ユーザーIDのマッピングを削除
        note_usernameが指定されていない場合は全てのマッピングを削除
        """
        try:
            if note_username:
                # 特定のnote.comユーザー名のマッピングを削除
                self.table.delete_item(
                    Key={
                        'line_user_id': line_user_id,
                        'note_username': note_username
                    }
                )
            else:
                # そのLINEユーザーIDの全てのマッピングを削除
                response = self.table.query(
                    KeyConditionExpression='line_user_id = :line_user_id',
                    ExpressionAttributeValues={
                        ':line_user_id': line_user_id
                    }
                )
                for item in response.get('Items', []):
                    self.table.delete_item(
                        Key={
                            'line_user_id': line_user_id,
                            'note_username': item['note_username']
                        }
                    )
            return True
        except ClientError as e:
            print(f"Error deleting user mapping: {e}")
            return False

    def get_user_mapping(self, line_user_id: str) -> Optional[str]:
        """
        LINE ユーザーIDから note.com ユーザー名を取得（後方互換性のため最初の1つを返す）
        """
        mappings = self.get_user_mappings(line_user_id)
        return mappings[0] if mappings else None

    def get_user_mappings(self, line_user_id: str) -> List[str]:
        """
        LINE ユーザーIDから全てのnote.com ユーザー名を取得
        """
        try:
            response = self.table.query(
                KeyConditionExpression='line_user_id = :line_user_id',
                ExpressionAttributeValues={
                    ':line_user_id': line_user_id
                }
            )
            return [item['note_username'] for item in response.get('Items', [])]
        except ClientError as e:
            print(f"Error getting user mappings: {e}")
            return []

    def get_all_user_mappings(self) -> List[Dict[str, str]]:
        """
        すべてのユーザーマッピングを取得
        """
        try:
            response = self.table.scan()
            return response.get('Items', [])
        except ClientError as e:
            print(f"Error getting all user mappings: {e}")
            return []

    def get_all_line_user_ids(self) -> List[str]:
        """
        すべてのLINE ユーザーIDを取得
        """
        try:
            response = self.table.scan(
                ProjectionExpression='line_user_id'
            )
            return [item['line_user_id'] for item in response.get('Items', [])]
        except ClientError as e:
            print(f"Error getting all line user IDs: {e}")
            return []