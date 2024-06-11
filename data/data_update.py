from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, MetaData, Table, select, update
from sqlalchemy.orm import sessionmaker
import pandas as pd


# CSV 파일 읽기
csv_file_path = 'song_copy.csv'
df = pd.read_csv(csv_file_path, encoding='utf-8-sig')


config = {
    'user': 'user',
    'password': 'jsql1445',
    'host': '13.125.27.204',
    'port': 3306,
    'database': 'cansingtone-schema',
    'raise_on_warnings': True
}


# 데이터베이스 연결
DATABASE_URL = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

metadata = MetaData()
songs_table = Table('song', metadata, autoload_with=engine)



# CSV 데이터 기반으로 데이터베이스 업데이트
for index, row in df.iterrows():
    song_id = row['index']
    song_vid_url = row['song_vid_url']
    highest_note80 = row['highest_note80']
    highest_note = row['highest_note']

    try:
        # 데이터베이스에서 해당 곡 찾기
        stmt = select(songs_table).where(songs_table.c.song_id == song_id)
        song = session.execute(stmt).fetchone()

        if song:
            # 업데이트할 데이터 준비
            update_data = {
                'song_vid_url': song_vid_url,
            }

            # highest_note80 값을 확인하여 업데이트할 필드 결정
            if pd.isna(highest_note80) or highest_note80 == -1:
                update_data['highest_note'] = highest_note
            else:
                update_data['highest_note'] = highest_note80

            # 데이터베이스 업데이트
            stmt = (
                update(songs_table)
                .where(songs_table.c.song_id == song_id)
                .values(update_data)
            )
            session.execute(stmt)
            session.commit()
            print(f'Song ID {song_id} updated successfully.')
        else:
            print(f'Song ID {song_id} not found in the database.')

    except SQLAlchemyError as e:
        print(f'Error updating Song ID {song_id}: {str(e)}')
        session.rollback()

# 세션 닫기
session.close()
