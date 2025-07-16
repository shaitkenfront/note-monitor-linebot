import pytest
import requests
from unittest.mock import patch, Mock
from app import note_scraper


class TestNoteScraperNewFeatures:
    """note_scraperの新機能のテスト"""
    
    @patch('requests.get')
    def test_get_dashboard_info_from_note_url_success(self, mock_get, sample_html_with_followers):
        """指定URLからフォロワー数を取得できること"""
        mock_response = Mock()
        mock_response.text = sample_html_with_followers
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = note_scraper.get_dashboard_info_from_note_url('https://note.com/test_user')
        
        assert 'error' not in result
        assert result['followers_count'] == 1234
        assert result['url'] == 'https://note.com/test_user'
        assert 'last_updated' in result
        
        mock_get.assert_called_once_with(
            'https://note.com/test_user',
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
            timeout=10
        )
    
    @patch('requests.get')
    def test_get_dashboard_info_from_note_url_empty_url(self, mock_get):
        """空のURLの場合はエラーを返すこと"""
        result = note_scraper.get_dashboard_info_from_note_url('')
        
        assert 'error' in result
        assert 'note.comのURLが指定されていません' in result['error']
        mock_get.assert_not_called()
    
    @patch('requests.get')
    def test_get_dashboard_info_from_note_url_none(self, mock_get):
        """NoneのURLの場合はエラーを返すこと"""
        result = note_scraper.get_dashboard_info_from_note_url(None)
        
        assert 'error' in result
        assert 'note.comのURLが指定されていません' in result['error']
        mock_get.assert_not_called()
    
    @patch('requests.get')
    def test_get_dashboard_info_from_note_url_request_error(self, mock_get):
        """リクエストエラーが発生した場合はエラーを返すこと"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        result = note_scraper.get_dashboard_info_from_note_url('https://note.com/test_user')
        
        assert 'error' in result
        assert 'リクエストエラー' in result['error']
    
    @patch('app.note_scraper.get_dashboard_info_from_note_url')
    @patch('app.note_scraper.format_dashboard_info_for_display')
    def test_get_note_dashboard_response_for_user(self, mock_format, mock_get_info):
        """指定ユーザーのダッシュボード情報取得が正しく動作すること"""
        mock_get_info.return_value = {'followers_count': 5678}
        mock_format.return_value = 'formatted response for user'
        
        result = note_scraper.get_note_dashboard_response_for_user('test_user')
        
        assert result == 'formatted response for user'
        mock_get_info.assert_called_once_with('https://note.com/test_user')
        mock_format.assert_called_once_with({'followers_count': 5678})
    
    @patch('app.note_scraper.get_dashboard_info_from_note')
    def test_get_note_dashboard_response_legacy_compatibility(self, mock_get_info):
        """既存のget_note_dashboard_response関数が正しく動作すること"""
        mock_get_info.return_value = {
            'followers_count': 1234,
            'url': 'https://note.com/test_user',
            'last_updated': '2023-01-01 12:00:00'
        }
        
        result = note_scraper.get_note_dashboard_response()
        
        assert '📊 note.com フォロワー数情報' in result
        assert '1,234人' in result
        mock_get_info.assert_called_once()
    
    @patch('requests.get')
    def test_get_dashboard_info_from_note_calls_url_version(self, mock_get, mock_environment_variables, sample_html_with_followers):
        """get_dashboard_info_from_noteが内部でget_dashboard_info_from_note_urlを呼び出すこと"""
        mock_response = Mock()
        mock_response.text = sample_html_with_followers
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = note_scraper.get_dashboard_info_from_note()
        
        assert 'error' not in result
        assert result['followers_count'] == 1234
        mock_get.assert_called_once_with(
            'https://note.com/test_user',
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
            timeout=10
        )
    
    def test_format_dashboard_info_for_display_large_numbers(self):
        """大きな数値が正しく整形されること"""
        dashboard_info = {
            'followers_count': 1234567,
            'url': 'https://note.com/popular_user',
            'last_updated': '2023-01-01 12:00:00'
        }
        
        result = note_scraper.format_dashboard_info_for_display(dashboard_info)
        
        assert '👥 フォロワー数: 1,234,567人' in result
        assert '👤 アカウント: popular_user' in result
    
    def test_format_dashboard_info_for_display_missing_fields(self):
        """必須フィールドが不足している場合のデフォルト値"""
        dashboard_info = {}
        
        result = note_scraper.format_dashboard_info_for_display(dashboard_info)
        
        assert '👥 フォロワー数: 0人' in result
        assert '👤 アカウント: Unknown' in result
        assert '🔗 URL: ' in result
    
    @patch('requests.get')
    def test_get_dashboard_info_from_note_url_complex_html(self, mock_get):
        """複雑なHTMLからフォロワー数を抽出できること"""
        complex_html = """
        <html>
        <head><title>Complex User - note</title></head>
        <body>
            <div class="profile-container">
                <div class="user-info">
                    <div class="stats">
                        <div class="stat-item">
                            <span class="stat-number">12,345</span>
                            <span class="stat-label">フォロワー</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">67</span>
                            <span class="stat-label">記事</span>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = complex_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = note_scraper.get_dashboard_info_from_note_url('https://note.com/complex_user')
        
        assert 'error' not in result
        assert result['followers_count'] == 12345
    
    @patch('requests.get')
    def test_get_dashboard_info_from_note_url_no_followers_html(self, mock_get):
        """フォロワー数が見つからないHTMLの場合"""
        no_followers_html = """
        <html>
        <head><title>No Followers - note</title></head>
        <body>
            <div class="profile">
                <h1>ユーザープロフィール</h1>
                <p>記事を投稿しています</p>
            </div>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = no_followers_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = note_scraper.get_dashboard_info_from_note_url('https://note.com/no_followers')
        
        assert 'error' not in result
        assert result['followers_count'] == 0
    
    @patch('requests.get')
    def test_get_dashboard_info_from_note_url_timeout(self, mock_get):
        """タイムアウトエラーが正しく処理されること"""
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        result = note_scraper.get_dashboard_info_from_note_url('https://note.com/test_user')
        
        assert 'error' in result
        assert 'リクエストエラー' in result['error']
        assert 'Request timeout' in result['error']
    
    @patch('requests.get')
    def test_get_dashboard_info_from_note_url_http_error(self, mock_get):
        """HTTPエラーが正しく処理されること"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        result = note_scraper.get_dashboard_info_from_note_url('https://note.com/not_found')
        
        assert 'error' in result
        assert 'リクエストエラー' in result['error']
        assert '404 Not Found' in result['error']
    
    def test_extract_number_from_text_various_formats(self):
        """様々な形式の数値テキストを正しく抽出できること"""
        # カンマ区切り
        assert note_scraper.extract_number_from_text('1,234,567') == 1234567
        
        # 前後にテキストがある場合
        assert note_scraper.extract_number_from_text('フォロワー: 1,234人') == 1234
        
        # 複数の数値がある場合（最初の数値を取得）
        assert note_scraper.extract_number_from_text('1,234フォロワー 567いいね') == 1234
        
        # 数値のみ
        assert note_scraper.extract_number_from_text('98765') == 98765
        
        # 0の場合
        assert note_scraper.extract_number_from_text('0') == 0
        
        # 小数点が含まれる場合（整数部分のみ）
        assert note_scraper.extract_number_from_text('1,234.56') == 1234
    
    def test_extract_number_from_text_edge_cases(self):
        """エッジケースの数値抽出テスト"""
        # 数値形式でない文字列
        assert note_scraper.extract_number_from_text('abc,def') == 0
        
        # 空のカンマ区切り
        assert note_scraper.extract_number_from_text(',,') == 0
        
        # 日本語の数値
        assert note_scraper.extract_number_from_text('１２３４') == 0  # 全角数字は抽出されない
        
        # 負の数値
        assert note_scraper.extract_number_from_text('-1,234') == 1234  # 負号は無視される