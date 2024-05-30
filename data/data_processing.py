import pandas as pd
import random
import re


# 함수 1: mr_vid_url 가공
def process_mr_vid_url(df):
    def modify_vid_url(vid_url):
        if vid_url.startswith("'"):
            vid_url = vid_url.strip("'")
        return f"https://www.youtube.com/watch?v={vid_url}"

    df['mr_vid_url'] = df['mr_vid_url'].apply(modify_vid_url)
    df.to_csv('processed_mr_vid_url.csv', index=False, encoding='utf-8-sig')


# 함수 2: album_image_url 가공
def process_album_image(df):
    def modify_album_url(url):
        if not url.startswith('http'):
            return f"https://{url}"
        return url

    df['album_image'] = df['album_image'].apply(modify_album_url)
    df.to_csv('processed_album_image.csv', index=False, encoding='utf-8-sig')


# 함수 3: gender_code에 따른 highest_note와 lowest_note 채우기
def fill_notes_based_on_gender(df):
    def assign_notes(row):
        gender_code = row['artist_gender_code']
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


def extract_feat_info(df):
    # feat_info 필드 추가 및 초기화
    df['feat_info'] = None
    
    # 각 row에 대해 artist 필드를 확인하고 (Feat.~~) 부분을 추출 및 제거
    for index, row in df.iterrows():
        artist = row['artist']
        # (Feat.~~) 부분 추출
        feat_match = re.search(r'\(feat.*$', artist, re.IGNORECASE)
        prod_match = re.search(r'\(prod.*$', artist, re.IGNORECASE)
        with_match = re.search(r'\(with.*$', artist, re.IGNORECASE)

        feat_info = feat_match.group(0) if feat_match else ""
        prod_info = prod_match.group(0) if prod_match else ""
        with_info = with_match.group(0) if with_match else ""

        max_length = max(len(feat_info), len(prod_info), len(with_info))

        if max_length > 0:
            # artist 필드에서 (Feat.~~) 부분 제거
            if len(feat_info) == max_length:
                artist = artist.replace(feat_info, '').strip()
                df.at[index, 'feat_info'] = feat_info
            elif len(prod_info) == max_length:
                artist = artist.replace(prod_info, '').strip()
                df.at[index, 'feat_info'] = prod_info
            elif len(with_info) == max_length:
                artist = artist.replace(with_info, '').strip()
                df.at[index, 'feat_info'] = with_info
            
            # DataFrame에 반영
            df.at[index, 'artist'] = artist
        else:
            df.at[index, 'feat_info'] = 'None'
    
    # 수정된 DataFrame을 processed_feat.csv 파일로 저장
    df.to_csv('processed_feat.csv', index=False, encoding='utf-8-sig')


def genre_encoding(df):
    # genre_code 필드 추가 및 초기화
    df['genre_code'] = None

    # 각 row에 대해 genre 필드를 확인
    for index, row in df.iterrows():
        genre = row['genre']
        
        if '록' in genre or '락' in genre or '메탈' in genre:
            df.at[index, 'genre_code'] = 5
        elif 'R&B' in genre or '블루스' in genre or '소울' in genre or '재즈' in genre:
            df.at[index, 'genre_code'] = 3
        elif '발라드' in genre:
            df.at[index, 'genre_code'] = 1
        elif '성인가요' in genre or '트로트' in genre:
            df.at[index, 'genre_code'] = 6
        elif '랩' in genre or '힙합' in genre:
            df.at[index, 'genre_code'] = 4
        elif '댄스' in genre or '일렉' in genre:
            df.at[index, 'genre_code'] = 2
        else:
            df.at[index, 'genre_code'] = 'None'
    
    df.to_csv('processed_genre.csv', index=False, encoding='utf-8-sig')


def gender_encoding(df):
    df['artist_gender_code'] = None

    for index, row in df.iterrows():
        artist_gender = row['artist_gender']
        feat_info = row['feat_info']
        
        if feat_info == "None" and artist_gender == "남성/솔로":
            df.at[index, 'artist_gender_code'] = 1
        elif feat_info == "None" and artist_gender == "여성/솔로":
            df.at[index, 'artist_gender_code'] = 2
        else:
            df.at[index, 'artist_gender_code'] = 3
    
    df.to_csv('processed_gender.csv', index=False, encoding='utf-8-sig')


if __name__ == "__main__":

    mr_vid_url_processing = False
    album_image_processing = False
    notes_processing = True
    feat_processing = False
    encode_genre = False
    encode_gender = False

    # CSV 파일 읽기
    file_path = 'song_copy.csv'
    df = pd.read_csv(file_path, encoding='utf-8-sig')

    # 함수 실행
    # 각 함수는 원본 df의 복사본에서 작업하여 독립적으로 실행
    if mr_vid_url_processing:
        process_mr_vid_url(df.copy())

    if album_image_processing:
        process_album_image(df.copy())

    if notes_processing:
        fill_notes_based_on_gender(df.copy())

    if feat_processing:
        extract_feat_info(df.copy())

    if encode_genre:
        genre_encoding(df.copy())

    if encode_gender:
        gender_encoding(df.copy())
