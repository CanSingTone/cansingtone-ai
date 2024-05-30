import csv
import re
from googleapiclient.discovery import build
from datetime import datetime, timedelta


# YouTube API 키 설정
api_key = [
    "AIzaSyBmfww6LKYPWg0I_SAgIaLkjZ77hybOcwk",
    "AIzaSyBiT3GZlzzCtDZMJBpHY7XFZT1PCCF9PA8",
    "AIzaSyDGBaopMLd04Vk_-icrNYIT2TsgIF357wI",
    "AIzaSyAYkycGQzKWtjp1rLCYGOiCLwZoWSA_Gbo",
    "AIzaSyA__FK1TUu3iCR64k86zXnneGhwaEqcDK0",
    "AIzaSyAIyAwINasnAkgTxsWLszQsJ0_QSVUzlCo",
    "AIzaSyAlMWtSOagZ4j-rNl9nCuJCe3N1T2c09uI",
    "AIzaSyA7g5f2Qp8FJ1ePsWQUOIuF2byntEHti_Y",
    "AIzaSyD2CvDj4Q0S5knGzyA505tsLVodwTIWUOE"
]




# 유튜브 API를 이용해 검색
def search_TJ(start_date, end_date):
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
            q="-노래방레전드 -메들리 -여자키 -남자키 -멜로디제거",
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


def search_song(song_title, artist, key):
    # YouTube API 클라이언트 생성
    youtube = build('youtube', 'v3', developerKey=key)
    # YouTube API를 사용하여 검색
    query = f"{song_title} {artist}"
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=1,  # 관련도가 가장 높은 1개의 결과만 가져옴
        type='video'
    ).execute()

    # 검색 결과에서 첫 번째 영상의 제목과 URL 추출
    if search_response['items']:
        video = search_response['items'][0]
        video_title = video['snippet']['title']
        video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
        return video_title, video_url
    else:
        return "None", "None"


def load_csv(filename):
    with open(filename, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        songs = [(row['song_title'], row['artist']) for row in reader]

    return songs


# csv파일로 저장
def save_csv(values, fieldnames, filename):
    # CSV 파일 열기 및 헤더 작성
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # CSV 파일에 쓰기
        for value in values:
            writer.writerow(dict(zip(fieldnames, value)))


# 안씀 참고용
def parse_song_info(videos):
    videos_info = []
    idx = 1
    # 각 동영상에 대한 정보 파싱
    for video in videos:
        video_id = video["id"]["videoId"]
        video_title = video["snippet"]["title"]
        video_description = video["snippet"]["description"]

        if video_id.startswith("-"):
            video_id = "'" + video_id + "'"
        song_title, artist = parse_title(video_title)
        karaoke_num = parse_karaoke_num(video_description)

        videos_info.append([idx, video_id, song_title, artist, karaoke_num])

        idx += 1

    return videos_info


# 영상 제목에서 노래 제목과 가수 파싱
def parse_title(title):
    try:
        # 제목과 가수 부분을 나눔
        parts = title.split(" - ")

        # "[TJ 노래방]" 부분을 제거하여 노래 제목 추출
        song_title = parts[0].replace("[TJ노래방]", "").strip()

        # " / TJ Karaoke" 부분을 제거하여 가수 이름 추출
        artist = parts[1].replace(" / TJ Karaoke", "").strip()

        return song_title, artist
    except IndexError:  # 인덱스 오류가 발생하면 빈 값 반환
        return title, ""


# 영상 정보에서 노래방 번호 파싱
def parse_karaoke_num(description):
    # 영상 정보를 줄 단위로 나눔
    lines = description.split('\n')

    flag1 = "TJ 노래방 곡번호"
    flag2 = "TJ노래방 곡번호"

    # 두 번째 줄에서 "TJ 노래방 곡번호."를 찾음
    for line in lines:
        if flag1 in line or flag2 in line:
            index1 = line.find(flag1)
            index2 = line.find(flag2)
            index = index1 + index2 + 1

            # 숫자 부분만 추출하여 노래방 번호로 간주
            match = re.search(r'\d+', line[index:])
            karaoke_num = match.group() if match else description
            return karaoke_num

    # "TJ 노래방 곡번호."가 없는 경우
    return description


if __name__ == "__main__":

    input_file_name = 'song_copy.csv'
    output_file_name = 'song_copy_url.csv'

    searchTJ = False

    if searchTJ:
        # 시작 날짜 설정 (2014년 6월 1일)
        start_date = datetime(2016, 1, 1)

        videos = []

        # 한 달씩 이동하며 검색하고 CSV 파일로 저장
        while start_date.year < 2017:# or start_date.month < 7:  # 2020년 11월 1일까지 검색
            end_date = start_date + timedelta(days=30)  # 한 달 간격으로 설정
            end_date = min(end_date, datetime(2017, 1, 1))  # 2020년 1월 1일까지만 검색
            videos.extend(search_TJ(start_date.strftime('%Y-%m-%dT%H:%M:%SZ'), 
                                    end_date.strftime('%Y-%m-%dT%H:%M:%SZ')))
            start_date = end_date

        fieldnames = ['index', 'mr_vid_url', 'song_title', 'artist', 'karaoke_num']
        videos_info = parse_song_info(videos)

        save_csv(videos_info, fieldnames, output_file_name)
    else:
        songs = load_csv(input_file_name)

        fieldnames = ['song_title', 'artist', 'video_title', 'song_vid_url']
        values = []

        idx = 0
        start = 900

        for i in range(start, len(songs)):
            song_title, artist = songs[i]
            video_title, song_url = search_song(song_title, artist, api_key[idx])
            print(i, [song_title, artist, video_title, song_url])
            values.append([song_title, artist, video_title, song_url])
            
            if (i+1) % 100 == 0:
                save_csv(values, fieldnames, str(idx) + output_file_name)
                values = []
                idx += 1
