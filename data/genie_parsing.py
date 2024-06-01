import requests
from bs4 import BeautifulSoup
import csv
import re


# CSV 파일에서 노래 제목과 가수 이름을 읽어옵니다.
def read_csv(filename):
    songs = []
    with open(filename, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            songs.append((row['song_title'], row['artist'], row['genie_id'], row['album_image']))
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


# Genie 사이트에서 곡 정보를 가져오는 함수
def parsing(song_title, artist):
    # 검색어 생성
    search_query = f"{artist} {song_title}"
    search_url = f"https://www.genie.co.kr/search/searchSong?query={search_query}"

    # 검색 결과 페이지 요청
    headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    if not soup:
        print("검색 페이지 HTTP 응답 오류", end='')
        return tuple("search HTTP error" for _ in range(6))

    # 검색 결과에서 첫 번째 곡 정보 페이지로 이동
    first_tr = soup.find('tr', class_='list')
    genie_id = None
    if first_tr:
        genie_id = first_tr.get('songid')
        print("첫 번째 검색 결과:", genie_id, end=' / ')
    else:
        print("검색 결과가 없습니다.", end=' / ')
        return tuple("Unknown" for _ in range(6))

    song_page_url = f"https://www.genie.co.kr/detail/songInfo?xgnm={genie_id}"

    # 곡 정보 페이지 요청
    response = requests.get(song_page_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    if not soup:
        print("곡 정보 페이지 HTTP 응답 오류", end='')
        return genie_id, tuple("song info HTTP error" for _ in range(5))

    # 노래 제목 가져오기
    finding_title_element = soup.find('h2', class_='name')

    finding_title = None
    if finding_title_element:
        finding_title = finding_title_element.get_text(strip=True)
        print(finding_title, end=' / ')
    else:
        print("제목X", end=' / ')

    # 가수 가져오기
    info_data_class = soup.find('ul', class_='info-data')

    finding_artist = None
    if info_data_class:
        li_tag = info_data_class.find('li')
        
        if li_tag:
            finding_artist_span = li_tag.find('span', class_='value')

            if finding_artist_span:
                finding_artist = finding_artist_span.get_text(strip=True)
                print(finding_artist, end=' / ')
            else:
                print("가수X", end=' / ')

    # 장르 정보 가져오기
    genre_element = soup.find('img', alt='장르')
    genre = None
    if genre_element:
        li_tag = genre_element.find_parent('li')

        if li_tag:
            genre_span = li_tag.find('span', class_='value')

            if genre_span:
                genre = genre_span.get_text(strip=True)
                print(genre, end=' / ')
            else:
                print("장르X", end=' / ')
    else:
        print("장르X", end=' / ')

    # 앨범 이미지 url 가져오기
    album_image_element = soup.find('a', class_='album2-thumb')

    album_image = None
    if album_image_element:
        album_image = album_image_element.get('href')
        album_image = album_image[2:] # 시작 부분 // 제거
        print(album_image, end=' / ')
    else:
        print("앨범이미지X", end=' / ')

    # 가수 id 가져오기

    # 검색어 생성
    search_url = f"https://www.genie.co.kr/search/searchArtist?query={artist}"

    # 검색 결과 페이지 요청
    headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    # <a> 태그를 찾고 onclick 속성의 값을 가져옴
    a_tag = soup.find('a', href="#", class_='thumb')
    artist_id = None
    if a_tag:
        img_tag = a_tag.find('img')

        if img_tag:
            src_value = img_tag['src']
        
            # 정규 표현식을 사용하여 숫자를 추출
            match = re.search(r"/(\d+)_", src_value)
            if match:
                artist_id = match.group(1)
                print(artist_id, end=' / ')

    # 가수 id가 있다면, 가수 성별 가져오기
    artist_gender = None
    if artist_id:
        artist_page_url = f"https://www.genie.co.kr/detail/artistInfo?xxnm={artist_id}"

        # 곡 정보 페이지 요청
        response = requests.get(artist_page_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        if not soup:
            print("가수 정보 페이지 HTTP 응답 오류", end='')
            return genie_id, finding_title, finding_artist, genre, album_image, "Unknown"
        
        artist_info_data_class = soup.find('ul', class_='info-data')
        
        if artist_info_data_class:
            li_tag = artist_info_data_class.find('li')
            
            if li_tag:
                gender_span = li_tag.find('span', class_='value')

                if gender_span:
                    artist_gender = gender_span.get_text(strip=True)
                    print(artist_gender, end=' / ')
                else:
                    print("성별X", end=' / ')
    else:
        print("artist_idX", end=' / ')
        

    return genie_id, finding_title, finding_artist, genre, album_image, artist_gender


def date_parsing(album_id):
    headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    song_page_url = f"https://www.genie.co.kr/detail/albumInfo?axnm={album_id}"

    # 곡 정보 페이지 요청
    response = requests.get(song_page_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    if not soup:
        print("곡 정보 페이지 HTTP 응답 오류", end='')
        return "Unknown"
    
    # 마지막 li 태그 찾기
    info_tag = soup.find('ul', class_='info-data') 
    last_li = info_tag.find_all('li')[-1]

    # 날짜 값 추출
    span = last_li.find('span', class_='value')
    date = span.get_text(strip=True) if span else "Unknown"

    return date


def extract_album_id(url):
    # 정규 표현식 패턴: 8-9글자 숫자
    pattern = r"/(\d{8,9})_"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


if __name__ == "__main__":

    parse_info = False
    parse_date = True

    # CSV 파일에서 노래 제목과 가수 이름을 읽어옵니다.
    songs = read_csv('song_copy.csv')

    if parse_info:
        # 각 곡에 대한 정보를 가져옵니다.
        songs_with_info = []
        for song_title, artist, genie_id in songs:
            print("찾을 대상: ", song_title, artist, end=' - ')
            genie_id, finding_title, finding_artist, genre, album_image, artist_gender = parsing(song_title, artist)
            songs_with_info.append([genie_id, finding_title, finding_artist, genre, album_image, artist_gender])

            print()

        fieldnames = ['genie_id', 'song_title', 'artist', 'genre', 'album_image', 'artist_gender']

        # 결과를 CSV 파일로 저장합니다.
        save_csv(songs_with_info, 'song_info.csv')

    if parse_date:
        songs_with_date = []
        for _, _, genie_id, album_image in songs:
            album_id = extract_album_id(album_image)
            print(album_id, album_image)

            date = date_parsing(album_id)
            
            songs_with_date.append([genie_id, date])
        
        fieldnames = ['genie_id', 'date']

        save_csv(songs_with_date, fieldnames=fieldnames, filename='song_date.csv')

