# note.com フォロワー数モニタリング LINE Bot

note.comのフォロワー数を定期的に監視し、LINE でユーザーに通知する Bot です。

## 🎯 主な機能

- **ユーザー登録**: note.com のユーザー名を LINE Bot に登録
- **複数アカウント対応**: 1人のLINEユーザーにつき最大3つのnote.comアカウントを登録可能
- **定期通知**: 設定したスケジュールでフォロワー数を自動取得・通知
- **リアルタイム応答**: 登録状況の確認や新規登録がリアルタイムで可能

## 🏗️ アーキテクチャ

このプロジェクトは AWS Lambda をベースとしたサーバーレスアーキテクチャです。

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LINE Platform │    │   API Gateway   │    │  AWS Lambda     │
│                 │◄──►│                 │◄──►│                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │   EventBridge   │◄────────────┤
                       │   (Scheduler)   │             │
                       └─────────────────┘             │
                                                        ▼
                                               ┌─────────────────┐
                                               │   DynamoDB      │
                                               │                 │
                                               └─────────────────┘
```

### 主要コンポーネント

- **`lambda_function.py`**: AWS Lambda のメインハンドラー
- **`app/line_handler.py`**: LINE Bot の Webhook 処理と署名検証
- **`app/db_handler.py`**: DynamoDB でのユーザー情報管理
- **`app/note_scraper.py`**: note.com からフォロワー数を取得
- **`app/validator.py`**: note.com ユーザー名の形式検証

## 🚀 セットアップ

### 前提条件

- Python 3.8 以上
- AWS アカウント
- LINE Developers アカウント

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 必要なライブラリ

```
boto3>=1.9.201
requests>=2.5
beautifulsoup4>=4.0.0
```

### 2. 環境変数の設定

以下の環境変数を設定してください：

#### LINE Bot 設定
```bash
export LINE_CHANNEL_ACCESS_TOKEN="your_line_channel_access_token"
export LINE_CHANNEL_SECRET="your_line_channel_secret"
```

#### DynamoDB 設定
```bash
export DYNAMODB_TABLE_NAME="note-monitor-users"  # オプション（デフォルト値使用可）
```

#### note.com 設定（レガシー機能用）
```bash
export NOTE_URL="https://note.com/your_username"  # オプション
```

### 3. DynamoDB テーブルの作成

AWS CLI または AWS コンソールで以下の設定でテーブルを作成してください：

```bash
aws dynamodb create-table \
    --table-name note-monitor-users \
    --attribute-definitions \
        AttributeName=line_user_id,AttributeType=S \
        AttributeName=note_username,AttributeType=S \
    --key-schema \
        AttributeName=line_user_id,KeyType=HASH \
        AttributeName=note_username,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST
```

### 4. LINE Bot の設定

1. [LINE Developers Console](https://developers.line.biz/) でチャンネルを作成
2. チャンネルアクセストークンとチャンネルシークレットを取得
3. Webhook URL を設定（API Gateway のエンドポイント）

### 5. AWS Lambda へのデプロイ

1. プロジェクトを ZIP ファイルに圧縮
2. AWS Lambda 関数を作成
3. 環境変数を設定
4. API Gateway でトリガーを設定
5. EventBridge で定期実行を設定

## 📱 使用方法

### ユーザー登録

LINE Bot に note.com のユーザー名を送信するだけで登録完了：

```
hekisaya
```

### 複数アカウントの登録

最大3つまでのアカウントを登録可能：

```
user1
user2  
user3
```

### 登録状況の確認

無効なメッセージを送信すると現在の登録状況が表示されます：

```
状況確認
```

### 登録解除

LINE Bot をブロック（アンフォロー）すると自動的に登録が削除されます。

## 🧪 テスト

### テストの実行

```bash
# 全テストを実行
pytest

# 特定のテストファイルを実行
pytest tests/test_lambda_function.py

# カバレッジレポート付きで実行
pytest --cov=app
```

### テストファイル構成

- `tests/test_db_handler.py`: DynamoDB ハンドラーのテスト
- `tests/test_lambda_function.py`: Lambda 関数のテスト
- `tests/test_lambda_function_limit.py`: 制限チェック機能のテスト
- `tests/test_line_handler.py`: LINE ハンドラーのテスト
- `tests/test_note_scraper.py`: note.com スクレイピングのテスト
- `tests/test_validator.py`: バリデーション機能のテスト

## 🔧 開発

### ローカル開発

```bash
# Lambda 関数をローカルでテスト
python lambda_function.py

# 個別モジュールのテスト
python -m app.line_handler
python -m app.note_scraper
```

### コードフォーマット

```bash
# コードフォーマット（推奨）
black .
isort .
```

## 📊 監視とログ

### CloudWatch Logs

Lambda 関数の実行ログは CloudWatch Logs で確認できます：

- エラーログ
- 実行時間
- メモリ使用量
- API 呼び出し状況

### メトリクス

以下のメトリクスを監視することを推奨：

- Lambda 関数の実行回数
- エラー率
- 実行時間
- DynamoDB の読み書き使用量

## 🛡️ セキュリティ

### LINE Webhook 署名検証

すべての LINE からのリクエストは署名検証を行い、正当性を確認しています。

### 環境変数の管理

機密情報は環境変数として管理し、コードにハードコーディングしていません。

### DynamoDB アクセス制御

IAM ロールを使用して必要最小限のアクセス権限のみを付与してください。

## 🚨 制限事項

- 1人のLINEユーザーにつき最大3つのnote.comアカウントまで登録可能
- note.com ユーザー名は3-16文字の英数字とアンダースコアのみ対応
- スクレイピングのため、note.com の仕様変更により動作しなくなる可能性があります

## 🐛 トラブルシューティング

### よくある問題

#### 1. LINE Bot が応答しない
- LINE チャンネルの設定を確認
- Webhook URL が正しく設定されているか確認
- Lambda 関数の実行ログを確認

#### 2. DynamoDB エラー
- テーブルが正しく作成されているか確認
- IAM ロールの権限を確認
- リージョンの設定を確認

#### 3. note.com からデータが取得できない
- ネットワーク接続を確認
- note.com のユーザー名が正しいか確認
- note.com の仕様変更の可能性を確認

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 🤝 コントリビューション

プルリクエストや Issue の報告を歓迎します！

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📞 サポート

問題や質問がある場合は、GitHub の Issues でお知らせください。

## 🔗 関連リンク

- [LINE Messaging API Documentation](https://developers.line.biz/ja/docs/messaging-api/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [note.com](https://note.com/)