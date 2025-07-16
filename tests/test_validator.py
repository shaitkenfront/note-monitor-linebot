import pytest
from app.validator import validate_note_username, extract_username_from_note_url, is_valid_note_url


class TestValidator:
    
    def test_validate_note_username_valid_short(self):
        """3文字の有効なユーザー名を検証できること"""
        assert validate_note_username('abc') is True
        assert validate_note_username('123') is True
        assert validate_note_username('a_b') is True
    
    def test_validate_note_username_valid_long(self):
        """16文字の有効なユーザー名を検証できること"""
        assert validate_note_username('abcdefghijklmnop') is True
        assert validate_note_username('1234567890123456') is True
        assert validate_note_username('a_b_c_d_e_f_g_h_') is True
    
    def test_validate_note_username_valid_mixed(self):
        """英数字とアンダースコアが混在する有効なユーザー名を検証できること"""
        assert validate_note_username('test_user') is True
        assert validate_note_username('user123') is True
        assert validate_note_username('note_user_2023') is True
        assert validate_note_username('hekisaya') is True
    
    def test_validate_note_username_invalid_too_short(self):
        """2文字以下の無効なユーザー名を検証できること"""
        assert validate_note_username('ab') is False
        assert validate_note_username('a') is False
        assert validate_note_username('') is False
    
    def test_validate_note_username_invalid_too_long(self):
        """17文字以上の無効なユーザー名を検証できること"""
        assert validate_note_username('abcdefghijklmnopq') is False
        assert validate_note_username('12345678901234567') is False
    
    def test_validate_note_username_invalid_characters(self):
        """無効な文字を含むユーザー名を検証できること"""
        assert validate_note_username('test-user') is False  # ハイフン
        assert validate_note_username('test.user') is False  # ドット
        assert validate_note_username('test user') is False  # スペース
        assert validate_note_username('test@user') is False  # アットマーク
        assert validate_note_username('test#user') is False  # シャープ
        assert validate_note_username('testユーザー') is False  # 日本語
    
    def test_validate_note_username_none(self):
        """Noneの場合は無効であること"""
        assert validate_note_username(None) is False
    
    def test_validate_note_username_empty_string(self):
        """空文字の場合は無効であること"""
        assert validate_note_username('') is False
    
    def test_extract_username_from_note_url_valid(self):
        """有効なnote.comのURLからユーザー名を抽出できること"""
        assert extract_username_from_note_url('https://note.com/hekisaya') == 'hekisaya'
        assert extract_username_from_note_url('http://note.com/test_user') == 'test_user'
        assert extract_username_from_note_url('https://note.com/user123') == 'user123'
    
    def test_extract_username_from_note_url_with_path(self):
        """パスが含まれるURLからユーザー名を抽出できること"""
        assert extract_username_from_note_url('https://note.com/hekisaya/n/abc123') == 'hekisaya'
        assert extract_username_from_note_url('https://note.com/test_user/followers') == 'test_user'
    
    def test_extract_username_from_note_url_invalid_domain(self):
        """note.com以外のドメインからは抽出できないこと"""
        assert extract_username_from_note_url('https://example.com/user') == ''
        assert extract_username_from_note_url('https://twitter.com/user') == ''
        assert extract_username_from_note_url('https://note.net/user') == ''
    
    def test_extract_username_from_note_url_invalid_format(self):
        """無効な形式のURLからは抽出できないこと"""
        assert extract_username_from_note_url('https://note.com/') == ''
        assert extract_username_from_note_url('https://note.com') == ''
        assert extract_username_from_note_url('note.com/user') == ''
    
    def test_extract_username_from_note_url_none(self):
        """Noneの場合は空文字を返すこと"""
        assert extract_username_from_note_url(None) == ''
    
    def test_extract_username_from_note_url_empty_string(self):
        """空文字の場合は空文字を返すこと"""
        assert extract_username_from_note_url('') == ''
    
    def test_is_valid_note_url_valid(self):
        """有効なnote.comのURLを検証できること"""
        assert is_valid_note_url('https://note.com/hekisaya') is True
        assert is_valid_note_url('http://note.com/test_user') is True
        assert is_valid_note_url('https://note.com/user123') is True
    
    def test_is_valid_note_url_invalid_username(self):
        """無効なユーザー名を含むURLを検証できること"""
        assert is_valid_note_url('https://note.com/ab') is False  # 短すぎる
        assert is_valid_note_url('https://note.com/abcdefghijklmnopq') is False  # 長すぎる
        assert is_valid_note_url('https://note.com/test-user') is False  # 無効文字
    
    def test_is_valid_note_url_invalid_domain(self):
        """note.com以外のドメインは無効であること"""
        assert is_valid_note_url('https://example.com/user') is False
        assert is_valid_note_url('https://twitter.com/user') is False
    
    def test_is_valid_note_url_invalid_format(self):
        """無効な形式のURLは無効であること"""
        assert is_valid_note_url('https://note.com/') is False
        assert is_valid_note_url('https://note.com') is False
        assert is_valid_note_url('note.com/user') is False
    
    def test_is_valid_note_url_none(self):
        """Noneの場合は無効であること"""
        assert is_valid_note_url(None) is False
    
    def test_is_valid_note_url_empty_string(self):
        """空文字の場合は無効であること"""
        assert is_valid_note_url('') is False
    
    def test_edge_cases_with_special_characters(self):
        """特殊な文字を含むエッジケースのテスト"""
        # 先頭・末尾のアンダースコア
        assert validate_note_username('_test') is True
        assert validate_note_username('test_') is True
        assert validate_note_username('_test_') is True
        
        # 連続するアンダースコア
        assert validate_note_username('test__user') is True
        assert validate_note_username('___') is True
        
        # 数字のみ
        assert validate_note_username('123456') is True
        
        # アンダースコアのみ
        assert validate_note_username('___') is True
        assert validate_note_username('________________') is True  # 16文字
    
    def test_boundary_values(self):
        """境界値のテスト"""
        # 3文字（最小）
        assert validate_note_username('abc') is True
        assert validate_note_username('12_') is True
        
        # 16文字（最大）
        assert validate_note_username('abcdefghijklmnop') is True
        assert validate_note_username('1234567890123456') is True
        
        # 2文字（最小-1）
        assert validate_note_username('ab') is False
        assert validate_note_username('1_') is False
        
        # 17文字（最大+1）
        assert validate_note_username('abcdefghijklmnopq') is False
        assert validate_note_username('12345678901234567') is False