import re

def validate_note_username(username: str) -> bool:
    """
    note.comのユーザー名形式を検証する
    ルール: 3-16文字の英数字とアンダースコアのみ
    """
    if not username:
        return False

    # 長さの確認
    if len(username) < 3 or len(username) > 16:
        return False

    # 文字種の確認（英数字とアンダースコアのみ）
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))

def extract_username_from_note_url(url: str) -> str:
    """
    note.comのURLからユーザー名を抽出する
    """
    if not url:
        return ""

    # note.com/username の形式から username を抽出
    pattern = r'https?://note\.com/([a-zA-Z0-9_]+)(?:/.*)?$'
    match = re.search(pattern, url)

    if match:
        return match.group(1)

    return ""

def is_valid_note_url(url: str) -> bool:
    """
    note.comの有効なURLかどうかを検証する
    """
    if not url:
        return False

    username = extract_username_from_note_url(url)
    return validate_note_username(username)