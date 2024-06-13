from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime, timedelta, timezone
import pickle
import random

import audio_processing.pitch as pitch
import audio_processing.timbre as timbre
import audio_processing.predict_song as predict

app = Flask(__name__)

@app.route('/',methods=['GET'])
def test():
    return "hello flask"

# 허용할 파일 확장자
ALLOWED_EXTENSIONS = {'mp3', 'aac'}

# 업로드된 파일이 허용된 확장자인지 확인하는 함수
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 음역대 테스트 파일을 받는 엔드포인트
@app.route('/upload-pitch', methods=['POST'])
def upload_pitch():
    # 파일이 전송되었는지 확인
    if 'file' not in request.files:
        return jsonify({'isSuccess': False, 'message': 'No file part in the request'}), 400
    
    file = request.files['file']  # This is a FileStorage object
    user_id = request.form['user_id']

    # 파일명이 없는 경우
    if file.filename == '':
        return jsonify({'isSuccess': False, 'message': 'No selected file'}), 400

    # 허용된 파일인지 확인
    if not (file and allowed_file(file.filename)):
        return jsonify({'isSuccess': False, 'message': 'File extension not allowed'}), 400
    
    # 파일 저장
    filename = file.filename
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    # 파일 경로를 pitch_processing 함수에 전달하여 분석
    highest_note, lowest_note = pitch.pitch_processing(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    if highest_note == -1 or lowest_note == -1:
        print("Pitch processing failed")
        return jsonify({'isSuccess': False, 'message': 'Pitch processing failed'}), 400

    pitch_url = f'http://13.125.27.204:8080/users/{user_id}/vocal-range'  # 서버주소는 애플리케이션이 실행되는 주소
    params = {
        'vocal_range_high': highest_note,
        'vocal_range_low': lowest_note
    }

    response = requests.patch(pitch_url, params=params)

    if response.status_code != 200:
        print("Pitch upload failed:", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Pitch upload failed'}), 400
    
    pitch_recommendation_url = 'http://13.125.27.204:8080/range-based-recommendations'
    data = {
        'user_id': user_id,
        'vocal_range_high': highest_note,
        'vocal_range_low': lowest_note
    }

    response = requests.post(pitch_recommendation_url, data=data)

    # 응답 처리
    if response.status_code == 200:
        print("Pitch-based-recommendation successfully: ", response.json())
        return jsonify({'isSuccess': True, 'message': 'Pitch-based-recommendation successfully', 'result': data}), 200
    else:
        print("Pitch-based-recommendation failed:", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Pitch-based-recommendation failed'}), 400


# 음색 테스트 파일을 받는 엔드포인트
# 파일과 유저id 받음
# 파일 mel 변환해서 s3 url 받고, 이를 음색 테이블에 저장
# 해당 mel 가지고 추천 수행, 추천곡10개 음색추천테이블에 저장
@app.route('/upload-timbre', methods=['POST'])
def upload_timbre():
    # 파일이 전송되었는지 확인
    if 'file' not in request.files:
        return jsonify({'isSuccess': False, 'message': 'No file part in the request'}), 400
    
    file = request.files['file']  # This is a FileStorage object
    user_id = request.form['user_id']

    response = requests.get(f'http://13.125.27.204:8080/users/{user_id}')
    response_json = response.json()

    if response.status_code != 200:
        print("Failed to retrieve user info", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Failed to retrieve user info'}), 400

    result_json = response_json.get('result', {})
    gender = result_json.get('gender')

    # 파일명이 없는 경우
    if file.filename == '':
        return jsonify({'isSuccess': False, 'message': 'No selected file'}), 400
    
    # 허용된 파일인지 확인
    if not (file and allowed_file(file.filename)):
        return jsonify({'isSuccess': False, 'message': 'File extension not allowed'}), 400

    # 파일 저장
    filename = file.filename
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    mel_path = timbre.timbre_processing(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    s3_url = 'http://13.125.27.204:8080/upload'
    files = {'file': open(mel_path, 'rb')}

    response = requests.post(s3_url, files=files)

    # 응답 처리
    if response.status_code != 200:
        print("Timbre upload failed:", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Timbre upload failed'}), 400
    
    # JSON 응답 데이터 파싱
    response_data = response.json()
    
    # uploadTimbre 값을 timbre_url 변수에 저장
    timbre_url = response_data.get("uploadTimbre")

    # s3 url과 유저id를 보내 db에 넣고 그 응답으로 오는 음색id 확인
    timbre_api_url = 'http://13.125.27.204:8080/timbre'  # 서버주소는 애플리케이션이 실행되는 주소
    timbre_info = {
        'timbre_url': timbre_url,
        'user_id': user_id
    }

    response = requests.post(timbre_api_url, data=timbre_info)

    # 응답 처리
    if response.status_code != 200:
        print("Timbre URL upload failed: ", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Timbre URL upload failed'}), 400
    
    response_json = response.json()
    timbre_id = response_json.get('result', {}).get('timbreId')

    if gender == 1:
        nb_classes = 232
    elif gender == 2:
        nb_classes = 116

    sorted_similarities = predict.predict_song(mel_path, 
                                    nb_classes=nb_classes,
                                    slice_length=157,
                                    random_states=21,
                                    activate=False,
                                    csv_file_path=f'activations_{nb_classes}_157_21.csv',)

    # 저장할 파일 경로를 설정합니다.
    file_path = f'similarities_{timbre_id}.pkl'

    # pickle을 사용해 딕셔너리를 파일로 저장합니다.
    with open(file_path, 'wb') as file:
        pickle.dump(sorted_similarities, file)

    print(f'Aggregated similarities have been saved to {file_path}')

    final_sorted_similarities = sorted(sorted_similarities, key=lambda x: x[1], reverse=True)
    indices = sorted(random.sample(range(15), 10))
    top_10_songs = [final_sorted_similarities[i] for i in indices]

    current_time_local = kst_time_now()
    song_ids = [song[0][2] for song in top_10_songs]

    # top10_songs에 song_id 정보 있으면 그걸로 song_id 대체하면 됨
    timbre_recommendations_url = 'http://13.125.27.204:8080/timbre-based-recommendations'  # 서버주소는 애플리케이션이 실행되는 주소
    recommendation = {
        'song_ids': song_ids,
        'user_id': user_id,
        'recommendation_date': current_time_local,
        'timbre_id': timbre_id
    }

    response = requests.post(timbre_recommendations_url, data=recommendation)

    # 응답 처리
    if response.status_code == 200:
        print("Timbre-based-recommendation successfully: ", response.json())
        return jsonify({'isSuccess': True, 'message': 'Timbre-based-recommendation successfully', 'result': recommendation}), 200
    else:
        print("Timbre-based-recommendation failed: ", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Timbre-based-recommendation failed'}), 400
    

# 음색 기반 추천곡 생성하는 엔드포인트
# 음색id, 유저id 받음
# 음색테이블에서 음색id로 해당하는 url 받음
# url 파일로 추천곡 10곡 생성
@app.route('/recommendation-timbre', methods=['POST'])
def recommendation_timbre():

    data = request.get_json()
    timbre_id = data['timbre_id']
    user_id = data['user_id']

    response = requests.get(f'http://13.125.27.204:8080/users/{user_id}')
    response_json = response.json()

    if response.status_code != 200:
        print("Failed to retrieve user info", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Failed to retrieve user info'}), 400
    
    result_json = response_json.get('result', {})
    gender = result_json.get('gender')

    # timbre_id로 음색 파일 URL을 얻기 위해 외부 API 호출
    response = requests.get(f'http://13.125.27.204:8080/timbre/{timbre_id}')
    if response.status_code != 200:
        print("Failed to retrieve timbre URL", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Failed to retrieve timbre URL'}), 400

    response_json = response.json()
    timbre_url = response_json.get('result', {}).get('timbreUrl')

    timbre_file_path = 'sample_data/timbre.mp3'
    response = requests.get(timbre_url)
    if response.status_code == 200:
        with open(timbre_file_path, 'wb') as file:
            file.write(response.content)
    else:
        print(f"Timbre file download failed: {response.status_code}")

    if gender == 1:
        nb_classes = 232
    elif gender == 2:
        nb_classes = 116

    # 파일 경로를 설정합니다.
    file_path = f'similarities_{timbre_id}.pkl'

    # pickle을 사용해 파일에서 딕셔너리를 불러옵니다.
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            loaded_aggregated_similarities = pickle.load(file)

        sorted_similarities = sorted(loaded_aggregated_similarities, key=lambda x: x[1], reverse=True)
        indices = sorted(random.sample(range(15), 10))
        top_10_songs = [sorted_similarities[i] for i in indices]
    else:
        top_10_songs = predict.predict_song(timbre_file_path, 
                                        nb_classes=nb_classes,
                                        slice_length=157,
                                        random_states=21,
                                        activate=False,
                                        csv_file_path=f'activations_{nb_classes}_157_21.csv',)


    current_time_local = kst_time_now()
    song_ids = [song[0][2] for song in top_10_songs]

    # top10_songs에 song_id 정보 있으면 그걸로 song_id 대체하면 됨
    recommendations_api_url = 'http://13.125.27.204:8080/timbre-based-recommendations'  # 서버주소는 애플리케이션이 실행되는 주소
    recommendation = {
        'song_ids': song_ids,
        'user_id': user_id,
        'recommendation_date': current_time_local,
        'timbre_id': timbre_id
    }

    response = requests.post(recommendations_api_url, data=recommendation)

    # 응답 처리
    if response.status_code == 200:
        print("Recommendation Update Successfully: ", response.json())
        return jsonify({'isSuccess': True, 'message': 'Timbre-based-recommendation successfully', 'result': recommendation}), 200
    else:
        print("Timbre-based-recommendation Failed: ", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Timbre-based-recommendation failed'}), 400


# 종합 추천곡 생성하는 엔드포인트
# 유저id 받음
# 음역대, 음색, 좋아요, 플리 정보 확인
# 추천곡 생성 및 저장
@app.route('/recommendation-combined', methods=['POST'])
def recommendation_combined():

    data = request.get_json()
    user_id = data['user_id']

    response = requests.get(f'http://13.125.27.204:8080/users/{user_id}')
    response_json = response.json()
    code = response_json.get('code')
    print("Response code: ", code, type(code))

    if code != 1000:
        print("Failed to retrieve user info", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Failed to retrieve user info'}), 400
    
    result_json = response_json.get('result', {})
    gender = result_json.get('gender')
    highest_note = result_json.get('vocal_range_high')
    lowest_note = result_json.get('vocal_range_low')
    pref_genre1 = result_json.get('pref_genre1')
    pref_genre2 = result_json.get('pref_genre2')
    pref_genre3 = result_json.get('pref_genre3')

    pref_genres = [pref_genre1, pref_genre2, pref_genre3]
    pref_genres = [genre for genre in pref_genres if genre]

    params = {
        'genres': pref_genres,
        'highest_note': highest_note + 2,
        'lowest_note': lowest_note - 2
    }

    response = requests.get('http://13.125.27.204:8080/songs/search', params=params)
    if response.status_code != 200:
        print("Failed to retrieve song info", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Failed to retrieve song info'}), 400

    response_json = response.json()
    result = response_json.get('result', {})

    song_pool = []
    for song in result:
        if song.get('artistGender') == gender:
            song_id = song.get('songId')
            song_pool.append(song_id)

    response = requests.get(f'http://13.125.27.204:8080/like/{user_id}')
    if response.status_code != 200:
        print("Failed to retrieve like info", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Failed to retrieve like info'}), 400
    
    response_json = response.json()
    #like_songs = [item.get('songInfo') for item in response_json.get('result', [])]

    like_artists = []

    # Iterate through each item in the result list
    for item in response_json.get('result', []):
        artist = item.get('songInfo', {}).get('artist')
        if artist:
            like_artists.append(artist)

    # 요청에 필요한 파라미터
    timbre_info_api = 'http://13.125.27.204:8080/timbre'
    params = {
        'user_id': user_id
    }

    response = requests.get(timbre_info_api, params=params)
    if response.status_code != 200:
        print("Failed to retrieve user's timbre info", response.status_code)
        return jsonify({'isSuccess': False, 'message': "Failed to retrieve user's timbre info"}), 400
    
    response_json = response.json()
    timbre_ids = [item.get('timbreId') for item in response_json.get('result', [])]


    similarities_combined = {}

    # 모든 timbre_id에 대해 루프를 돌면서 각 .pkl 파일을 불러옵니다.
    for timbre_id in timbre_ids:
        file_path = f'similarities_{timbre_id}.pkl'
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                loaded_similarities = pickle.load(file)
                # 유사도가 0.5를 넘는 항목만 필터링하여 합칩니다.
                for key, similarity in loaded_similarities:
                    if similarity > 0.5:
                        if key in similarities_combined:
                            if similarity > similarities_combined[key]:
                                similarities_combined[key] = similarity
                        else:
                            similarities_combined[key] = similarity

    sorted_similarities = sorted(similarities_combined.items(), key=lambda x: x[1], reverse=True)

    final_similarities = {}
    # sorted_similarities의 각 항목을 업데이트
    for key, similarity in sorted_similarities:
        artist, song, song_id = key
        similarity = similarity
        
        # like_artists에 속해있는 가수라면 유사도에 1.1을 곱함
        for like_artist in like_artists:
            if artist == like_artist or artist in like_artist:
                similarity *= 1.1
        
        # song_pool에 없는 song_id라면 유사도에 0을 곱함
        if song_id not in song_pool:
            similarity = 0
        
        # 업데이트된 유사도를 다시 저장
        final_similarities[key] = similarity

    final_sorted_similarities = sorted(final_similarities.items(), key=lambda x: x[1], reverse=True)

    indices = sorted(random.sample(range(15), 10))
    top_10_songs = [final_sorted_similarities[i] for i in indices]

    current_time_local = kst_time_now()
    if len(top_10_songs) < 10:
        indices = random.sample(range(len(song_pool)), 10)
        song_ids = [song_pool[i] for i in indices]
    else:
        song_ids = [song[0][2] for song in top_10_songs]

    # top10_songs에 song_id 정보 있으면 그걸로 song_id 대체하면 됨
    recommendations_api_url = 'http://13.125.27.204:8080/combine-recommendations'  # 서버주소는 애플리케이션이 실행되는 주소
    recommendation = {
        'song_ids': song_ids,
        'user_id': user_id,
        'recommendation_date': current_time_local,
    }

    response = requests.post(recommendations_api_url, data=recommendation)

    # 응답 처리
    if response.status_code == 200:
        print("Combine-recommendation successfully: ", response.json())
        return jsonify({'isSuccess': True, 'message': 'Combine-recommendation successfully', 'result': recommendation}), 200
    else:
        print("Combine-recommendation failed: ", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Combine-recommendation failed'}), 400


def kst_time_now():
    # 서울 시간대 설정
    KST = timezone(timedelta(hours=9))

    # 현재 UTC 시간 가져오기
    current_time_utc = datetime.now(timezone.utc)

    # 서울 시간으로 변환
    current_time_seoul = current_time_utc.astimezone(KST)

    # 지정된 형식으로 변환
    current_time_local = current_time_seoul.strftime('%Y-%m-%d %H:%M:%S')

    return current_time_local



if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
