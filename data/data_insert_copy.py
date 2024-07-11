import pandas as pd
import mysql.connector
from mysql.connector import errorcode

# CSV 파일 읽기
file_path = 'song_copy_pers_chart.csv'
df = pd.read_csv(file_path, encoding='utf-8-sig')

# song_id 열 추가: index
df['song_id'] = df['index']

# gender_code -> artist_gender, genre_code -> genre 변환
df['artist_gender'] = df['artist_gender_code']
df['genre'] = df['genre_code']

df['highest_note'] = df.apply(lambda row: row['highest_note'] if pd.isna(row['highest_note80']) else row['highest_note80'], axis=1)
df['lowest_note'] = df.apply(lambda row: row['lowest_note'] if pd.isna(row['lowest_note80']) else row['lowest_note80'], axis=1)

df['song_title'] = df.apply(lambda row: row['song_title'] + ' ' + row['feat_info'] if pd.notnull(row['feat_info']) else row['song_title'], axis=1)

# 필요한 열만 선택하여 새로운 DataFrame 생성
db_df = df[['artist_gender', 'genre', 'highest_note', 'lowest_note', 'song_id', 'artist', 'mr_vid_url', 'song_title', 'song_vid_url', 'album_image', 'karaoke_num', 'prefer_age', 'prefer_gender', 'ranking']].copy()

# 열 이름을 데이터베이스 필드 이름에 맞게 변경
db_df.rename(columns={
    'artist_gender': 'artist_gender',
    'genre': 'genre',
    'highest_note': 'highest_note',
    'lowest_note': 'lowest_note',
    'song_id': 'song_id',
    'artist': 'artist',
    'mr_vid_url': 'mr_vid_url',
    'song_title': 'song_title',
    'song_vid_url': 'song_vid_url',
    'album_image': 'album_image',
    'karaoke_num': 'karaoke_num',
    'prefer_age': 'prefer_age',
    'prefer_gender': 'prefer_gender',
    'ranking': 'ranking'
}, inplace=True)

# MySQL 데이터베이스 연결 설정
config = {
    'user': 'user',
    'password': 'jsql1445',
    'host': '13.125.27.204',
    'port': 3306,
    'database': 'cansingtone-schema',
    'raise_on_warnings': True
}

conn = None
cursor = None

try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    # DataFrame 데이터를 MySQL 테이블에 삽입
    for index, row in db_df.iterrows():
        #print(f"index: {index}, row: {row}")
        insert_query = """
        INSERT INTO personalized_chart (artist_gender, genre, highest_note, lowest_note, song_id, artist, mr_vid_url, song_title, song_vid_url, album_image, karaoke_num, prefer_age, prefer_gender, ranking)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            row['artist_gender'], row['genre'], row['highest_note'], row['lowest_note'],
            row['song_id'], row['artist'], row['mr_vid_url'], row['song_title'],
            row['song_vid_url'], row['album_image'], row['karaoke_num'], row['prefer_age'], row['prefer_gender'], row['ranking']
        ))

    # 커밋
    conn.commit()

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("사용자 이름 또는 비밀번호가 잘못되었습니다.")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("데이터베이스가 존재하지 않습니다.")
    else:
        print(err)
finally:
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()
