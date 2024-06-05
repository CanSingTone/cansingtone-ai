import os
import re
import shutil
import pandas as pd

def strip_name(directory, outliers_directory):
    # 디렉토리의 모든 파일 목록 가져오기
    for filename in os.listdir(directory):

        if filename.startswith('.'):
            continue

        # 현재 파일의 전체 경로
        full_path = os.path.join(directory, filename)
        
        # 파일 이름 패턴 매칭
        match = re.match(r'^\d+_\d+_\d+_(.*?)_\(Vocals\)_\(Vocals\)_\(No Reverb\) pyaudacity\.mp3$', filename)
        
        if match:
            # 새로운 파일 이름 생성
            name = match.group(1)
            new_filename = f"{name}.mp3"

            # 파일 이름에 '-' 문자가 두 번 포함되어 있는지 확인
            # 파일 이름에 '_', '/', '\' 문자가 포함되어 있는지 확인
            if new_filename.count('-') >= 2 or any(char in new_filename for char in ['_', '/', '\\', '|', ':', '*', '+', '=',
                                                                            '~', '₩', '?', '@', '\#', '%',
                                                                            '^', '<', '>', '"', ';']):
                # 파일을 outliers_directory로 이동
                shutil.move(full_path, os.path.join(outliers_directory, new_filename))
                print(f'Moved: {new_filename} -> {outliers_directory}')
            else:
                # 새로운 파일의 전체 경로
                new_full_path = os.path.join(directory, new_filename)
                
                # 파일 이름 변경
                os.rename(full_path, new_full_path)
                print(f'Renamed: {filename} -> {new_filename}')
        else:
            print(f'No match for: {filename}')


def add_song_id(directory, outliers_directory, csv_file):
    # sample_outliers 디렉토리가 존재하지 않으면 생성
    if not os.path.exists(outliers_directory):
        os.makedirs(outliers_directory)

    # CSV 파일 읽기
    df = pd.read_csv(csv_file)

    # artist와 song_title을 조합한 새로운 컬럼 생성
    df['combined'] = df['genie_artist'] + ' - ' + df['genie_song_title']

    # source_directory의 모든 파일 목록 가져오기
    for filename in os.listdir(directory):

        if filename.startswith('.'):
            continue

        # 현재 파일의 전체 경로
        full_path = os.path.join(directory, filename)
        
        if filename.endswith('.mp3'):
            # .mp3 확장자를 제외한 파일 이름 추출
            name_without_ext = filename[:-4]
            
            # CSV 데이터와 비교
            match = df[df['combined'] == name_without_ext]
            
            if not match.empty:
                # 매칭되는 경우 song_id 값을 읽어 새 파일 이름 생성
                artist = match['genie_artist'].values[0]
                song_title = match['genie_song_title'].values[0]
                song_id = match['index'].values[0]
                new_filename = f"{artist}__{song_title}__{song_id}.mp3"
                new_full_path = os.path.join(directory, new_filename)
                
                # 파일 이름 변경
                os.rename(full_path, new_full_path)
                print(f'Renamed: {filename} -> {new_filename}')
            else:
                # 매칭되지 않는 파일은 sample_outliers 디렉토리로 이동
                shutil.move(full_path, os.path.join(outliers_directory, filename))
                print(f'Moved: {filename} -> {outliers_directory}')
        else:
            print(f'No action for non-mp3 file: {filename}')



if __name__ == "__main__":

    # 디렉토리 경로 설정
    directory = 'sample_vad2'
    outliers_directory = 'sample_outliers'
    csv_file = 'song_copy.csv'

    name_stripping = False
    song_id_adding = not name_stripping

    if name_stripping:
        strip_name(directory, outliers_directory)

    if song_id_adding:
        add_song_id(directory, outliers_directory, csv_file)
    