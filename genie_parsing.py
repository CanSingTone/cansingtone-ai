import requests
from bs4 import BeautifulSoup
import csv


# CSV 파일에서 노래 제목과 가수 이름을 읽어옵니다.
def read_csv(filename):
    songs = []
    with open(filename, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            songs.append((row['song_title'], row['artist']))
    return songs


# CSV 파일에 장르 정보를 저장하는 함수
def save_to_csv(songs_with_genre, output_filename):
    with open(output_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['song_id', 'song_title', 'artist', 'genre', 'album_image_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for song in songs_with_genre:
            writer.writerow({'song_id': song[0], 'song_title': song[1], 'artist': song[2], 'genre': song[3], 'album_image_url': song[4]})


# Genie 사이트에서 곡 정보를 가져오는 함수
def parsing(song_title, artist):
    # 검색어 생성
    search_query = f"{song_title} {artist}"
    search_url = f"https://www.genie.co.kr/search/searchSong?query={search_query}"

    # 검색 결과 페이지 요청
    headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    if not soup:
        print("1차 HTTP 응답 오류", end='')
        return tuple("HTTP error" for _ in range(5))

    # 검색 결과에서 첫 번째 곡 정보 페이지로 이동
    first_tr = soup.find('tr', class_='list')
    songid = None
    if first_tr:
        songid = first_tr.get('songid')
        print("첫 번째 검색 결과:", songid, end=' / ')
    else:
        print("검색 결과가 없습니다.", end=' / ')
        return tuple("Unknown" for _ in range(5))

    song_page_url = f"https://www.genie.co.kr/detail/songInfo?xgnm={songid}"

    # 곡 정보 페이지 요청
    response = requests.get(song_page_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    if not soup:
        print("2차 HTTP 응답 오류", end='')
        return tuple("HTTP error" for _ in range(5))

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

    album_image_url = None
    if album_image_element:
        album_image_url = album_image_element.get('href')
        album_image_url = album_image_url[2:] # 시작 부분 // 제거
        print(album_image_url, end=' / ')
    else:
        print("앨범이미지X", end=' / ')
    
    return songid, finding_title, finding_artist, genre, album_image_url


if __name__ == "__main__":
    # CSV 파일에서 노래 제목과 가수 이름을 읽어옵니다.
    songs = read_csv('song_2.csv')

    # 각 곡에 대한 장르 정보를 가져옵니다.
    songs_with_genre = []
    for song_title, artist in songs:
        print("찾을 대상: ", song_title, artist, end=' - ')
        song_id, finding_title, finding_artist, genre, album_image_url = parsing(song_title, artist)
        songs_with_genre.append((song_id, finding_title, finding_artist, genre, album_image_url))

        print()

    # 결과를 CSV 파일로 저장합니다.
    save_to_csv(songs_with_genre, 'song_info.csv')