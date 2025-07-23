import os
import requests
import re
from datetime import datetime

def get_dashboard_info_from_note():
    """
    環境変数で指定されたnote.comのURLからフォロワー数を取得する
    """
    note_url = os.environ.get('NOTE_URL')

    if not note_url:
        return {
            'error': 'NOTE_URLが設定されていません。環境変数にnote.comのURLを設定してください。'
        }

    return get_dashboard_info_from_note_url(note_url)

def get_dashboard_info_from_note_url(note_url: str):
    """
    指定されたnote.comのURLからフォロワー数を取得する
    """
    if not note_url:
        print('The note.com URL variable is empty.')
        return {
            'error': 'note.comのURLが指定されていません。'
        }

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(note_url, headers=headers, timeout=20)
        response.raise_for_status()

        # フォロワー数は生のHTMLから'\"followerCount\" :'の後に続く数値を取得する
        if 'followerCount' not in response.text:
            print('"followerCount" is not found.')
            print(response.text)
            return {'error': 'フォロワー数の情報が見つかりません。URLが正しいか確認してください。'}
        follower_count_match = re.search(r'\\"followerCount\\"\s*:\s*(\d+)', response.text)
        if follower_count_match:
            followers_count = int(follower_count_match.group(1))
        else:
            print('The followers count regex did not match.')
            print(response.text)
            followers_count = 0

    except requests.exceptions.RequestException as e:
        print('A request error occurred.')
        return {'error': f'リクエストエラー: {str(e)}'}
    except Exception as e:
        print('A unexcepted error occurred.')
        return {'error': f'予期しないエラー: {str(e)}'}

    return {
        'followers_count': followers_count,
        'url': note_url,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


def extract_number_from_text(text):
    """
    テキストから数値を抽出する
    """
    if not text:
        return 0

    # 数値とカンマを抽出（半角数字のみ）
    numbers = re.findall(r'[0-9,]+', str(text))

    if numbers:
        # カンマを除去して数値に変換
        try:
            return int(numbers[0].replace(',', ''))
        except ValueError:
            return 0

    return 0

def format_dashboard_info_for_display(dashboard_info):
    """
    ダッシュボード情報を表示用に整形する
    """
    if 'error' in dashboard_info:
        return f"❌ エラー: {dashboard_info['error']}"

    followers = dashboard_info.get('followers_count', 0)
    url = dashboard_info.get('url', '')

    # アカウント名をURLから抽出
    account_name = url.split('/')[-1] if url else 'Unknown'

    # 数値をカンマ区切りで表示
    formatted_followers = f"{followers:,}"

    message = f"""👤 アカウント: {account_name}
👥 フォロワー数: {formatted_followers}人"""

    return message

def get_note_dashboard_response():
    """
    note.comのフォロワー数情報を取得し、整形された応答を返す
    """
    dashboard_info = get_dashboard_info_from_note()
    return format_dashboard_info_for_display(dashboard_info)

def get_note_dashboard_response_for_user(note_username: str):
    """
    指定されたnote.comユーザーのフォロワー数情報を取得し、整形された応答を返す
    """
    note_url = f"https://note.com/{note_username}"
    dashboard_info = get_dashboard_info_from_note_url(note_url)
    return format_dashboard_info_for_display(dashboard_info)
