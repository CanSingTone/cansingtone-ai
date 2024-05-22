import pandas as pd
import random
import csv


# 함수 1: karaoke_vid_id 가공
def process_karaoke_vid_id(df):
    def modify_vid_id(vid_id):
        if vid_id.startswith("'"):
            vid_id = vid_id.strip("'")
        return f"https://www.youtube.com/watch?v={vid_id}"

    df['karaoke_vid_id'] = df['karaoke_vid_id'].apply(modify_vid_id)
    df.to_csv('processed_karaoke_vid_id.csv', index=False, encoding='utf-8-sig')

# 함수 2: album_image_url 가공
def process_album_image_url(df):
    def modify_album_url(url):
        if not url.startswith('http'):
            return f"https://{url}"
        return url

    df['album_image_url'] = df['album_image_url'].apply(modify_album_url)
    df.to_csv('processed_album_image_url.csv', index=False, encoding='utf-8-sig')

# 함수 3: gender_code에 따른 highest_note와 lowest_note 채우기
def fill_notes_based_on_gender(df):
    def assign_notes(row):
        gender_code = row['gender_code']
        if gender_code == 1:
            row['lowest_note'] = random.randint(40, 50)
            row['highest_note'] = random.randint(60, 70)
        elif gender_code == 2:
            row['lowest_note'] = random.randint(50, 60)
            row['highest_note'] = random.randint(65, 75)
        elif gender_code == 3:
            row['lowest_note'] = random.randint(40, 60)
            row['highest_note'] = random.randint(60, 75)
        return row

    df = df.apply(assign_notes, axis=1)
    df.to_csv('processed_notes.csv', index=False, encoding='utf-8-sig')


if __name__ == "__main__":

    youtube_url_processing = False
    album_image_url_processing = False
    notes_processing = True

    # CSV 파일 읽기
    file_path = 'song_test.csv'
    df = pd.read_csv(file_path, encoding='utf-8-sig')

    # 함수 실행
    # 각 함수는 원본 df의 복사본에서 작업하여 독립적으로 실행
    if youtube_url_processing:
        process_karaoke_vid_id(df.copy())

    if album_image_url_processing:
        process_album_image_url(df.copy())

    if notes_processing:
        fill_notes_based_on_gender(df.copy())
