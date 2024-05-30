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
            songs.append((row['song_title'], row['artist'], row['genre']))
    return songs


# CSV 파일에 장르 정보를 저장하는 함수
def save_to_csv(songs_with_genre, output_filename):
    with open(output_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['melon_id', 'song_title', 'artist', 'genre']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for song in songs_with_genre:
            writer.writerow({'melon_id': song[0], 'song_title': song[1], 'artist': song[2], 'genre': song[3]})


# Genie 사이트에서 곡 정보를 가져오는 함수
def parsing(song_title, artist):
    # 검색어 생성
    search_query = f"{artist} {song_title}"
    search_url = f"https://www.melon.com/search/song/index.htm?q={search_query}"

    # 검색 결과 페이지 요청
    headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    if not soup:
        print("검색 페이지 HTTP 응답 오류", end='')
        return tuple("search HTTP error" for _ in range(6))

    # 검색 결과에서 첫 번째 곡 정보 페이지로 이동
    first_td = soup.find('td')
    first_div = first_td.find('div', class_='wrap pd_none left') if first_td else None
    melon_id = None
    if first_div:
        input_tag = first_div.find('input')

        if input_tag:
            melon_id = input_tag.get('value')
            print("첫 번째 검색 결과:", melon_id, end=' / ')
        else:
            print("검색 결과가 없습니다.", end=' / ')
            return tuple("Unknown" for _ in range(2))
    else:
        print("검색 결과가 없습니다.", end=' / ')
        return tuple("Unknown" for _ in range(2))

    song_page_url = f"https://www.melon.com/song/detail.htm?songId={melon_id}"

    # 곡 정보 페이지 요청
    response = requests.get(song_page_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    if not soup:
        print("곡 정보 페이지 HTTP 응답 오류", end='')
        return melon_id, tuple("song info HTTP error" for _ in range(1))

    # 장르 정보 가져오기
    genre_dl = soup.find('dl', class_='list')
    genre = ""
    if genre_dl:
        genre_dds = genre_dl.find_all('dd')

        for dd in genre_dds[1:]:
            genre = genre + dd.get_text(strip=True)
        print(genre, end='')
    else:
        print("장르X", end='')

    return melon_id, genre


if __name__ == "__main__":
    # CSV 파일에서 노래 제목과 가수 이름을 읽어옵니다.
    songs = read_csv('song_copy.csv')

    # 각 곡에 대한 정보를 가져옵니다.
    songs_with_genre = []
    for song_title, artist, genre in songs:
        if genre not in ['가요 / 전체', 'OST / 한국영화', 'POP / 팝', 'POP / 중국음악', 'OST / 전체', 'OST / 애니메이션/게임', 'OST / 뮤지컬/공연', 'OST / 드라마', '가요 / 인디']:
            continue
        print("찾을 대상: ", song_title, artist, end=' - ')
        melon_id, genre  = parsing(song_title, artist)
        songs_with_genre.append((melon_id, song_title, artist, genre))

        print()

    # 결과를 CSV 파일로 저장합니다.
    save_to_csv(songs_with_genre, 'song_melon_info.csv')
