import csv
import re
from googleapiclient.discovery import build

# 유튜브 API를 이용, TJ 노래방 채널에 있는 노래들의 정보를 파싱하고 csv파일에 저장
def collect_song_from_youtube_to_csv():
    # YouTube API 키 설정
    api_key = "AIzaSyD-pJKn-K1Tbt6PNeakowD77_FAQEmAER8"

    # YouTube API 클라이언트 생성
    youtube = build('youtube', 'v3', developerKey=api_key)

    # TJ 노래방 채널 ID
    channel_id = "UCZUhx8ClCv6paFW7qi3qljg"

    # CSV 파일 경로 설정
    csv_filename = "song1.csv"

    # 인덱스
    idx = 1
    
    """    
    print(youtube.channels().list(
        part="statistics",
        id=channel_id,
    ))
    return
    """

    # CSV 파일 열기 및 헤더 작성
    with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['Index', 'Video ID', 'Song Title', 'Artist', 'Karaoke Number', 'Page Token']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # 페이징 처리를 위한 변수 설정
        next_page_token = None

        while True:
            # 채널의 동영상 목록 가져오기
            playlist_items = youtube.playlistItems().list(
                part="snippet",
                playlistId="UU" + channel_id[2:],  # "UC"를 "UU"로 변경하여 사용
                maxResults=40,
                pageToken=next_page_token,
            ).execute()

            # 각 동영상에 대한 정보 파싱 및 CSV에 쓰기
            for item in playlist_items["items"]:
                video_id = item["snippet"]["resourceId"]["videoId"]
                video_title = item["snippet"]["title"]
                video_description = item["snippet"]["description"].split('\n')

                # video_description의 첫째 줄에서 노래 제목과 가수 이름 파싱
                first_line = video_description[0] if len(video_description) > 0 else ""
                song_title, artist = "", ""
                if '--' in first_line:
                    parts = first_line.split('--')
                    song_title = parts[0].strip()
                    artist = parts[1].strip()

                # video_description의 둘째 줄에서 노래방 번호 파싱
                second_line = video_description[1] if len(video_description) > 1 else ""
                match = re.search(r'\d{1,5}', second_line)
                karaoke_num = match.group() if match else ""

                #print(idx, video_id, song_title, artist, karaoke_num)

                # CSV 파일에 쓰기
                writer.writerow({'Index': idx,'Video ID': video_id, 'Song Title': song_title, 'Artist': artist, 'Karaoke Number': karaoke_num, 'Page Token': next_page_token})

                idx += 1

            # 다음 페이지 토큰 가져오기
            next_page_token = playlist_items.get('nextPageToken')

            #print(next_page_token)

            # 마지막 페이지인 경우 종료
            if not next_page_token:
                break


if __name__ == "__main__":
    collect_song_from_youtube_to_csv()
