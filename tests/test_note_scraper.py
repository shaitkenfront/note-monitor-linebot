import pytest
import requests
from unittest.mock import patch, Mock
from app import note_scraper


class TestNoteScraper:
    
    def test_extract_number_from_text_with_comma(self):
        """カンマ区切りの数値を正しく抽出できること"""
        result = note_scraper.extract_number_from_text("1,234")
        assert result == 1234
    
    def test_extract_number_from_text_without_comma(self):
        """カンマなしの数値を正しく抽出できること"""
        result = note_scraper.extract_number_from_text("1234")
        assert result == 1234
    
    def test_extract_number_from_text_with_text(self):
        """テキスト内の数値を正しく抽出できること"""
        result = note_scraper.extract_number_from_text("フォロワー数: 1,234人")
        assert result == 1234
    
    def test_extract_number_from_text_no_number(self):
        """数値がない場合は0を返すこと"""
        result = note_scraper.extract_number_from_text("フォロワー")
        assert result == 0
    
    def test_extract_number_from_text_empty(self):
        """空文字の場合は0を返すこと"""
        result = note_scraper.extract_number_from_text("")
        assert result == 0
    
    def test_extract_number_from_text_none(self):
        """Noneの場合は0を返すこと"""
        result = note_scraper.extract_number_from_text(None)
        assert result == 0

    @patch('requests.get')
    def test_get_dashboard_info_from_note_success(self, mock_get, mock_environment_variables, sample_html_with_followers):
        """正常にフォロワー数を取得できること"""
        mock_response = Mock()
        mock_response.text = sample_html_with_followers
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = note_scraper.get_dashboard_info_from_note()
        
        assert 'error' not in result
        assert result['followers_count'] == 1234
        assert result['url'] == 'https://note.com/test_user'
        assert 'last_updated' in result
        
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_dashboard_info_from_note_no_followers(self, mock_get, mock_environment_variables, sample_html_without_followers):
        """フォロワー数が見つからない場合は0を返すこと"""
        mock_response = Mock()
        mock_response.text = sample_html_without_followers
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = note_scraper.get_dashboard_info_from_note()
        
        assert 'error' not in result
        assert result['followers_count'] == 0
        assert result['url'] == 'https://note.com/test_user'
    
    def test_get_dashboard_info_from_note_no_url(self, monkeypatch):
        """NOTE_URLが設定されていない場合はエラーを返すこと"""
        monkeypatch.delenv('NOTE_URL', raising=False)
        
        result = note_scraper.get_dashboard_info_from_note()
        
        assert 'error' in result
        assert 'NOTE_URLが設定されていません' in result['error']
    
    @patch('requests.get')
    def test_get_dashboard_info_from_note_request_error(self, mock_get, mock_environment_variables):
        """リクエストエラーが発生した場合はエラーを返すこと"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        result = note_scraper.get_dashboard_info_from_note()
        
        assert 'error' in result
        assert 'リクエストエラー' in result['error']
    
    @patch('requests.get')
    def test_get_dashboard_info_from_note_timeout(self, mock_get, mock_environment_variables):
        """タイムアウトが発生した場合はエラーを返すこと"""
        mock_get.side_effect = requests.exceptions.Timeout("Timeout error")
        
        result = note_scraper.get_dashboard_info_from_note()
        
        assert 'error' in result
        assert 'リクエストエラー' in result['error']
    
    def test_format_dashboard_info_for_display_success(self):
        """正常なダッシュボード情報を正しく整形できること"""
        dashboard_info = {
            'followers_count': 1234,
            'url': 'https://note.com/test_user',
            'last_updated': '2023-01-01 12:00:00'
        }
        
        result = note_scraper.format_dashboard_info_for_display(dashboard_info)
        
        assert '📊 note.com フォロワー数情報' in result
        assert '👤 アカウント: test_user' in result
        assert '👥 フォロワー数: 1,234人' in result
        assert '🔗 URL: https://note.com/test_user' in result
        assert '🕐 最終更新: 2023-01-01 12:00:00' in result
    
    def test_format_dashboard_info_for_display_error(self):
        """エラー情報を正しく整形できること"""
        dashboard_info = {
            'error': 'テストエラー'
        }
        
        result = note_scraper.format_dashboard_info_for_display(dashboard_info)
        
        assert '❌ エラー: テストエラー' in result
    
    def test_format_dashboard_info_for_display_zero_followers(self):
        """フォロワー数が0の場合も正しく整形できること"""
        dashboard_info = {
            'followers_count': 0,
            'url': 'https://note.com/test_user',
            'last_updated': '2023-01-01 12:00:00'
        }
        
        result = note_scraper.format_dashboard_info_for_display(dashboard_info)
        
        assert '👥 フォロワー数: 0人' in result
    
    @patch('app.note_scraper.get_dashboard_info_from_note')
    @patch('app.note_scraper.format_dashboard_info_for_display')
    def test_get_note_dashboard_response(self, mock_format, mock_get_info):
        """get_note_dashboard_responseが正しく動作すること"""
        mock_get_info.return_value = {'followers_count': 1234}
        mock_format.return_value = 'formatted response'
        
        result = note_scraper.get_note_dashboard_response()
        
        assert result == 'formatted response'
        mock_get_info.assert_called_once()
        mock_format.assert_called_once_with({'followers_count': 1234})