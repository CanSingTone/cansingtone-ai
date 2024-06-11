import os
import shutil
import pandas as pd

# 디렉토리 경로
source_dir = 'sample_data/all'
dest_dir = 'sample_data/all_pitch'

# 목적지 디렉토리가 존재하지 않으면 생성
os.makedirs(dest_dir, exist_ok=True)

# CSV 파일 경로
csv_file = 'song_copy_pitch.csv'

# CSV 파일 읽기
df = pd.read_csv(csv_file)

# song_id 목록 생성
song_ids = df['index'].astype(str).tolist()

# 파일 이동 함수
def move_files_with_ids(source, destination, ids):
    for filename in os.listdir(source):
        if filename.endswith('.mp3'):
            # 파일명에서 song_id 추출
            parts = filename[:-4].split('__')
            if len(parts) == 3:
                song_id = parts[2].strip("_")
                if song_id in ids:
                    # 파일 이동
                    shutil.move(os.path.join(source, filename), os.path.join(destination, filename))
                    print(f'Moved: {filename}')
                else:
                    print(f"Song_id not in csv: {filename}")
            else:
                print(f"Parsing failed: {filename}")

# 파일 이동
move_files_with_ids(source_dir, dest_dir, song_ids)
