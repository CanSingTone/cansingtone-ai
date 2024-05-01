import csv
import re
from googleapiclient.discovery import build
from datetime import datetime, timedelta


# 유튜브 API를 이용해 검색
def search_songs(start_date, end_date):
    # YouTube API 키 설정
    api_key = "AIzaSyD-pJKn-K1Tbt6PNeakowD77_FAQEmAER8"

    # YouTube API 클라이언트 생성
    youtube = build('youtube', 'v3', developerKey=api_key)

    # TJ 노래방 채널 ID
    channel_id = "UCZUhx8ClCv6paFW7qi3qljg"

    # 페이징 처리를 위한 변수 설정
    next_page_token = None

    videos = []

    while True:
        # 채널의 동영상 목록 가져오기
        search_response = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            type="video",
            q="-노래방레전드 -메들리",
            maxResults=50,
            pageToken=next_page_token,
            publishedAfter=start_date,
            publishedBefore=end_date
        ).execute()

        videos.extend(search_response["items"])

        # 다음 페이지 토큰 가져오기
        next_page_token = search_response.get('nextPageToken')

        # 마지막 페이지인 경우 종료
        if not next_page_token:
            break

    return videos


# csv파일로 저장
def save_songs_to_csv(videos):
    # CSV 파일 경로 설정
    csv_filename = "song2.csv"

    # 인덱스
    idx = 1

    # CSV 파일 열기 및 헤더 작성
    with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['Index', 'Video ID', 'Song Title', 'Artist', 'Karaoke Number']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # 각 동영상에 대한 정보 파싱 및 CSV에 쓰기
        for video in videos:
            video_id = video["id"]["videoId"]
            video_title = video["snippet"]["title"]
            video_description = video["snippet"]["description"]

            song_title, artist, karaoke_num = parse_song_info(video_description)

            # CSV 파일에 쓰기
            writer.writerow({'Index': idx,'Video ID': video_id, 'Song Title': song_title, 'Artist': artist, 'Karaoke Number': karaoke_num})

            idx += 1


def parse_song_info(video_description):
    # 줄 별로 split
    video_description = video_description.split('\n')

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

    return song_title, artist, karaoke_num


if __name__ == "__main__":

    # 시작 날짜 설정 (2014년 6월 1일)
    start_date = datetime(2014, 6, 1)

    videos = []

    # 한 달씩 이동하며 검색하고 CSV 파일로 저장
    while start_date.year < 2016:# or start_date.month < 11:  # 2020년 11월 1일까지 검색
        end_date = start_date + timedelta(days=30)  # 한 달 간격으로 설정
        end_date = min(end_date, datetime(2016, 1, 1))  # 2020년 11월 1일까지만 검색
        videos.extend(search_songs(start_date.strftime('%Y-%m-%dT%H:%M:%SZ'), 
                                end_date.strftime('%Y-%m-%dT%H:%M:%SZ')))
        start_date = end_date

    save_songs_to_csv(videos)
