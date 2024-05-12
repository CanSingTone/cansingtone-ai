import pandas as pd
import requests

# Last.fm API 키
LASTFM_API_KEY = "ab1c5fd06149216ffda5dde303e5e67a"

# Last.fm API 요청 URL
API_URL = "http://ws.audioscrobbler.com/2.0/"

# song.csv 파일 경로
csv_file = "song_copy.csv"

# CSV 파일 읽기
df = pd.read_csv(csv_file, encoding='utf-8-sig')

# track name-artist pair list 생성하는 함수
def get_track_list(song_title, artist_name):
    params = {
        "method": "track.search",
        "track": song_title,
        "artist": artist_name,
        "api_key": LASTFM_API_KEY,
        "limit": 30,
        "format": "json"
    }
    response = requests.get(API_URL, params=params)
    data = response.json()
    tracks = data["results"]["trackmatches"]["track"]
    track_list = []
    for track in tracks:
        track_list.append((track["name"], track["artist"]))

    return track_list


# 앨범 이미지 URL을 가져오는 함수
def get_album_image(song_title, artist_name):

    album_image = get_album_image_from_track(song_title, artist_name)

    if album_image:
        return album_image

    track_list = get_track_list(song_title, artist_name)

    for name, artist in track_list:
        album_image = get_album_image_from_track(name, artist)

        if album_image:
            return album_image  # 이미지 URL 반환
        else:
            continue

    return None   # 이미지가 없을 경우 None 반환

def get_album_image_from_track(song_title, artist_name):
    params = {
        "method": "track.getInfo",
        "track": song_title,
        "artist": artist_name,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }
    response = requests.get(API_URL, params=params)
    data = response.json()
    if "track" in data and "album" in data["track"]:
        album_image_list = data["track"]["album"]["image"]
        
        for album_image in album_image_list[::-1]:
            if album_image["#text"]:
                print(song_title, artist_name, album_image["size"])
                return album_image["#text"]  # 이미지 URL 반환
    else:
        return None

# 각 노래의 앨범 이미지 URL 가져와서 H 열에 저장
album_images = []
for idx, row in df.iterrows():
    song_title = row['song_title']
    artist = row['artist']
    album_image = get_album_image(song_title, artist)
    if album_image:
        album_images.append(album_image)
        print(f"앨범 이미지 URL을 찾았습니다: {album_image}")
    else:
        album_images.append("Not Found")
        print(f"앨범 이미지를 찾을 수 없습니다. {song_title}, {artist}")

# H 열에 앨범 이미지 URL 추가
df['H'] = album_images

# CSV 파일로 저장
df.to_csv("song_with_album_url.csv", index=False, encoding='utf-8-sig')
