import os
import shutil

# 폴더 내의 모든 파일 목록을 가져오는 함수
def list_files(directory):
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    return [f for f in files if not f.startswith('.')]

# 파일 이름에서 아티스트 이름 추출하는 함수
def extract_artist(file_name):
    return file_name.split('__')[0]

# 아티스트 별 곡 수를 계산하는 함수
def count_songs_by_artist(files):
    artist_count = {}
    for file in files:
        artist = extract_artist(file)
        artist_count[artist] = artist_count.get(artist, 0) + 1
    return artist_count

# 곡 수가 3개 이상인 아티스트를 찾는 함수
def find_artists_with_three_or_more_songs(artist_count):
    return [artist for artist, count in artist_count.items() if count >= 3]

# 아티스트별 폴더를 생성하고 파일을 해당 폴더로 이동하는 함수
def organize_files(directory, files):
    artist_count = count_songs_by_artist(files)
    artists_to_move = find_artists_with_three_or_more_songs(artist_count)
    
    for artist in artists_to_move:
        artist_folder = os.path.join(directory, artist)
        os.makedirs(artist_folder, exist_ok=True)
        dir_names_path = 'sample_data/dir_names'
        os.makedirs(dir_names_path, exist_ok=True)
        os.makedirs(os.path.join(dir_names_path, artist), exist_ok=True)
        for file in files:
            if extract_artist(file) == artist:
                shutil.move(os.path.join(directory, file), os.path.join(artist_folder, file))

# 작업할 디렉토리 설정
directory = 'sample_data/all_solo'

# 디렉토리 내의 모든 파일 가져오기
files = list_files(directory)

# 파일을 아티스트 별로 정리
organize_files(directory, files)
