import pytest
from app.validator import validate_note_username, extract_username_from_note_url, is_valid_note_url


class TestNoteUsernameValidator:
    """note.comのユーザー名バリデーション - t_wada流テスト設計"""

    class TestValidCases:
        """有効なユーザー名のテスト"""

        def test_最小文字数3文字の場合_有効と判定される(self):
            # Given: 最小文字数の有効なユーザー名
            username = "abc"
            
            # When: バリデーションを実行
            result = validate_note_username(username)
            
            # Then: 有効と判定される
            assert result is True

        def test_最大文字数16文字の場合_有効と判定される(self):
            # Given: 最大文字数の有効なユーザー名
            username = "abcdefghijklmnop"  # 16文字
            
            # When: バリデーションを実行
            result = validate_note_username(username)
            
            # Then: 有効と判定される
            assert result is True

        def test_英数字アンダースコア混在の場合_有効と判定される(self):
            # Given: 英数字とアンダースコアが混在するユーザー名
            test_cases = [
                "test_user",
                "user123", 
                "note_user_2023",
                "hekisaya",
                "_test_",
                "123_abc_456"
            ]
            
            for username in test_cases:
                # When: バリデーションを実行
                result = validate_note_username(username)
                
                # Then: 有効と判定される
                assert result is True, f"'{username}' should be valid"

        def test_数字のみの場合_有効と判定される(self):
            # Given: 数字のみのユーザー名
            username = "123456"
            
            # When: バリデーションを実行
            result = validate_note_username(username)
            
            # Then: 有効と判定される
            assert result is True

        def test_アンダースコアのみの場合_有効と判定される(self):
            # Given: アンダースコアのみのユーザー名
            test_cases = ["___", "________________"]  # 3文字、16文字
            
            for username in test_cases:
                # When: バリデーションを実行
                result = validate_note_username(username)
                
                # Then: 有効と判定される
                assert result is True, f"'{username}' should be valid"


    class TestInvalidLength:
        """文字数による無効ケースのテスト"""

        def test_2文字以下の場合_無効と判定される(self):
            # Given: 文字数が少なすぎるユーザー名
            test_cases = ["", "a", "ab"]
            
            for username in test_cases:
                # When: バリデーションを実行
                result = validate_note_username(username)
                
                # Then: 無効と判定される
                assert result is False, f"'{username}' should be invalid (too short)"

        def test_17文字以上の場合_無効と判定される(self):
            # Given: 文字数が多すぎるユーザー名
            test_cases = [
                "abcdefghijklmnopq",  # 17文字
                "abcdefghijklmnopqr",  # 18文字
                "12345678901234567890"  # 20文字
            ]
            
            for username in test_cases:
                # When: バリデーションを実行
                result = validate_note_username(username)
                
                # Then: 無効と判定される
                assert result is False, f"'{username}' should be invalid (too long)"


    class TestInvalidCharacters:
        """無効文字によるテスト"""

        def test_ハイフンを含む場合_無効と判定される(self):
            # Given: ハイフンを含むユーザー名
            username = "test-user"
            
            # When: バリデーションを実行
            result = validate_note_username(username)
            
            # Then: 無効と判定される
            assert result is False

        def test_ドットを含む場合_無効と判定される(self):
            # Given: ドットを含むユーザー名
            username = "test.user"
            
            # When: バリデーションを実行
            result = validate_note_username(username)
            
            # Then: 無効と判定される
            assert result is False

        def test_特殊文字を含む場合_無効と判定される(self):
            # Given: 様々な特殊文字を含むユーザー名
            test_cases = [
                "test user",    # スペース
                "test@user",    # アットマーク
                "test#user",    # ハッシュ
                "test%user",    # パーセント
                "test&user",    # アンパサンド
                "test(user)",   # 括弧
            ]
            
            for username in test_cases:
                # When: バリデーションを実行
                result = validate_note_username(username)
                
                # Then: 無効と判定される
                assert result is False, f"'{username}' should be invalid (special chars)"

        def test_日本語を含む場合_無効と判定される(self):
            # Given: 日本語を含むユーザー名
            test_cases = [
                "testユーザー",
                "テストuser",
                "こんにちは"
            ]
            
            for username in test_cases:
                # When: バリデーションを実行
                result = validate_note_username(username)
                
                # Then: 無効と判定される
                assert result is False, f"'{username}' should be invalid (contains Japanese)"


    class TestNullAndEmpty:
        """NULL・空値のテスト"""

        def test_Noneの場合_無効と判定される(self):
            # Given: None値
            username = None
            
            # When: バリデーションを実行
            result = validate_note_username(username)
            
            # Then: 無効と判定される
            assert result is False

        def test_空文字の場合_無効と判定される(self):
            # Given: 空文字
            username = ""
            
            # When: バリデーションを実行
            result = validate_note_username(username)
            
            # Then: 無効と判定される
            assert result is False


class TestUrlUsernameExtraction:
    """URLからユーザー名抽出のテスト"""

    class TestValidExtraction:
        """正常な抽出ケース"""

        def test_基本的なURLから正しくユーザー名が抽出される(self):
            # Given: 基本的なnote.comのURL
            test_cases = [
                ("https://note.com/hekisaya", "hekisaya"),
                ("http://note.com/test_user", "test_user"),
                ("https://note.com/user123", "user123")
            ]
            
            for url, expected_username in test_cases:
                # When: URLからユーザー名を抽出
                result = extract_username_from_note_url(url)
                
                # Then: 正しいユーザー名が抽出される
                assert result == expected_username, f"Expected '{expected_username}' from '{url}'"

        def test_パスが含まれるURLからユーザー名が抽出される(self):
            # Given: パスが含まれるURL
            test_cases = [
                ("https://note.com/hekisaya/n/abc123", "hekisaya"),
                ("https://note.com/test_user/followers", "test_user"),
                ("https://note.com/user123/following", "user123")
            ]
            
            for url, expected_username in test_cases:
                # When: URLからユーザー名を抽出
                result = extract_username_from_note_url(url)
                
                # Then: 正しいユーザー名が抽出される
                assert result == expected_username


    class TestInvalidExtraction:
        """抽出失敗ケース"""

        def test_note_com以外のドメインの場合_空文字が返される(self):
            # Given: note.com以外のドメインのURL
            test_cases = [
                "https://example.com/user",
                "https://twitter.com/user",
                "https://note.net/user"
            ]
            
            for url in test_cases:
                # When: URLからユーザー名を抽出
                result = extract_username_from_note_url(url)
                
                # Then: 空文字が返される
                assert result == "", f"'{url}' should return empty string"

        def test_無効な形式のURLの場合_空文字が返される(self):
            # Given: 無効な形式のURL
            test_cases = [
                "https://note.com/",
                "https://note.com",
                "note.com/user",
                "not_a_url"
            ]
            
            for url in test_cases:
                # When: URLからユーザー名を抽出
                result = extract_username_from_note_url(url)
                
                # Then: 空文字が返される
                assert result == "", f"'{url}' should return empty string"

        def test_Noneまたは空文字の場合_空文字が返される(self):
            # Given: Noneまたは空文字
            test_cases = [None, ""]
            
            for url in test_cases:
                # When: URLからユーザー名を抽出
                result = extract_username_from_note_url(url)
                
                # Then: 空文字が返される
                assert result == ""


class TestUrlValidation:
    """URL全体の妥当性検証のテスト"""

    class TestValidUrls:
        """有効なURLのテスト"""

        def test_有効なnote_comのURLの場合_有効と判定される(self):
            # Given: 有効なnote.comのURL
            test_cases = [
                "https://note.com/hekisaya",
                "http://note.com/test_user",
                "https://note.com/user123"
            ]
            
            for url in test_cases:
                # When: URL妥当性を検証
                result = is_valid_note_url(url)
                
                # Then: 有効と判定される
                assert result is True, f"'{url}' should be valid"


    class TestInvalidUrls:
        """無効なURLのテスト"""

        def test_無効なユーザー名を含むURLの場合_無効と判定される(self):
            # Given: 無効なユーザー名を含むURL
            test_cases = [
                "https://note.com/ab",  # 短すぎる
                "https://note.com/abcdefghijklmnopq",  # 長すぎる
                "https://note.com/test-user"  # 無効文字
            ]
            
            for url in test_cases:
                # When: URL妥当性を検証
                result = is_valid_note_url(url)
                
                # Then: 無効と判定される
                assert result is False, f"'{url}' should be invalid"

        def test_note_com以外のドメインの場合_無効と判定される(self):
            # Given: note.com以外のドメインのURL
            test_cases = [
                "https://example.com/valid_user",
                "https://twitter.com/valid_user"
            ]
            
            for url in test_cases:
                # When: URL妥当性を検証
                result = is_valid_note_url(url)
                
                # Then: 無効と判定される
                assert result is False

        def test_不正な形式のURLの場合_無効と判定される(self):
            # Given: 不正な形式のURL
            test_cases = [
                "https://note.com/",
                "https://note.com",
                "note.com/user",
                None,
                ""
            ]
            
            for url in test_cases:
                # When: URL妥当性を検証
                result = is_valid_note_url(url)
                
                # Then: 無効と判定される
                assert result is False, f"'{url}' should be invalid"


    class TestBoundaryConditions:
        """境界条件のテスト"""

        def test_境界値でのユーザー名を含むURLの妥当性(self):
            # Given: 境界値のユーザー名を含むURL
            boundary_cases = [
                ("https://note.com/abc", True),  # 3文字（最小有効）
                ("https://note.com/abcdefghijklmnop", True),  # 16文字（最大有効）
                ("https://note.com/ab", False),  # 2文字（最小無効）
                ("https://note.com/abcdefghijklmnopq", False)  # 17文字（最大無効）
            ]
            
            for url, expected in boundary_cases:
                # When: URL妥当性を検証
                result = is_valid_note_url(url)
                
                # Then: 期待される結果と一致する
                assert result is expected, f"'{url}' should be {expected}"