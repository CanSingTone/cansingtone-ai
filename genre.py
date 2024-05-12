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

# Genie 사이트에서 곡 정보를 가져오는 함수
def get_genre(song_title, artist):
    # 검색어 생성
    search_query = f"{song_title} {artist}"
    search_url = f"https://www.genie.co.kr/search/searchMain?query={search_query}"

    # 검색 결과 페이지 요청
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # 검색 결과에서 첫 번째 곡 정보 페이지로 이동
    first_song_link = soup.find('a', {'class': 'title ellipsis'}).get('href')
    song_page_url = f"https://www.genie.co.kr{first_song_link}"

    # 곡 정보 페이지 요청
    response = requests.get(song_page_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # 장르 정보 가져오기
    genre = soup.find('dt', text='장르').find_next_sibling('dd').text.strip()
    return genre

# CSV 파일에 장르 정보를 저장하는 함수
def save_to_csv(songs_with_genre, output_filename):
    with open(output_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['song_title', 'artist', 'genre']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for song in songs_with_genre:
            writer.writerow({'song_title': song[0], 'artist': song[1], 'genre': song[2]})
    

if __name__ == "__main__":
    # CSV 파일에서 노래 제목과 가수 이름을 읽어옵니다.
    songs = read_csv('song_3.csv')

    # 각 곡에 대한 장르 정보를 가져옵니다.
    songs_with_genre = []
    for song_title, artist in songs:
        genre = get_genre(song_title, artist)
        songs_with_genre.append((song_title, artist, genre))

    # 결과를 CSV 파일로 저장합니다.
    save_to_csv(songs_with_genre, 'songs_with_genre.csv')
