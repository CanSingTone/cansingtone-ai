from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

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
        print("Pitch processing failed:", response.status_code)
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

    top10_songs = predict.predict_song(mel_path, activate=False)

    current_time_local = datetime.now().isoformat()
    song_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

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

    timbre_id = request.form['timbre_id']
    user_id = request.form['user_id']
    
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

    top10_songs = predict.predict_song(timbre_file_path, activate=False)

    current_time_local = datetime.now().isoformat()
    song_ids = [11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

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

    user_id = request.form['user_id']

    response = requests.get(f'http://13.125.27.204:8080/users/{user_id}')
    if response.status_code != 200:
        print("Failed to retrieve user info", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Failed to retrieve user info'}), 400
    
    response_json = response.json()
    result_json = response_json.get('result', {})
    gender = result_json.get('gender')
    highest_note = result_json.get('vocal_range_high')
    lowest_note = result_json.get('vocal_range_low')
    pref_genre1 = result_json.get('pref_genre1')
    pref_genre2 = result_json.get('pref_genre2')
    pref_genre3 = result_json.get('pref_genre3')

    response = requests.get(f'http://13.125.27.204:8080/like/{user_id}')
    if response.status_code != 200:
        print("Failed to retrieve like info", response.status_code)
        return jsonify({'isSuccess': False, 'message': 'Failed to retrieve like info'}), 400
    
    response_json = response.json()
    like_songs = [item.get('songInfo') for item in response_json.get('result', [])]

    response = requests.get(f'http://13.125.27.204:8080/timbre')
    if response.status_code != 200:
        print("Failed to retrieve user's timbre info", response.status_code)
        return jsonify({'isSuccess': False, 'message': "Failed to retrieve user's timbre info"}), 400
    
    response_json = response.json()
    timbre_urls = [item.get('timbreUrl') for item in response_json.get('result', [])]

    current_time_local = datetime.now().isoformat()
    song_ids = [21, 22, 23, 24, 25, 26, 27, 28, 29, 30]

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


if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
