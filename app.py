from flask import Flask, request, jsonify
import requests
import os

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
        return jsonify({'message': 'No file part in the request'}), 400
    
    file = request.files['file']  # This is a FileStorage object
    user_id = request.form['user_id']

    # 파일명이 없는 경우
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    # 허용된 파일인지 확인
    if file and allowed_file(file.filename):
        # 파일 저장
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # 파일 경로를 pitch_processing 함수에 전달하여 분석
        highest_note, lowest_note = pitch.pitch_processing(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        url = 'http://13.125.27.204:8080/users/{userId}/vocal-range'  # 서버주소는 애플리케이션이 실행되는 주소
        full_url = url.format(userId=user_id)
        params = {
            'vocal_range_high': highest_note,
            'vocal_range_low': lowest_note
        }

        response = requests.patch(full_url, params=params)

        # 응답 처리
        if response.status_code == 200:
            print("Pitch Update Successfully: ", response.json())
            
            return jsonify({'message': 'File uploaded successfully', 'highest_note': highest_note, 'lowest_note': lowest_note, 'user_id': user_id}), 200
        else:
            print("Pitch Update Failed:", response.status_code)

            return jsonify({'message': 'Pitch upload failed'}), 400
        
        
    else:
        return jsonify({'message': 'File extension not allowed'}), 400
    

# 음색 테스트 파일을 받는 엔드포인트
@app.route('/upload-timbre', methods=['POST'])
def upload_timbre():
    # 파일이 전송되었는지 확인
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400
    
    file = request.files['file']  # This is a FileStorage object
    user_id = request.form['user_id']

    # 파일명이 없는 경우
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    # 허용된 파일인지 확인
    if file and allowed_file(file.filename):
        # 파일 저장
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        mel_path = timbre.timbre_processing(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        s3_url = 'http://13.125.27.204:8080/upload'
        files = {'file': open(mel_path, 'rb')}

        response = requests.post(s3_url, files=files)

        # 응답 처리
        if response.status_code == 200:
            print("File Uploaded")
            
            # JSON 응답 데이터 파싱
            response_data = response.json()
            
            # uploadTimbre 값을 timbre_url 변수에 저장
            timbre_url = response_data.get("uploadTimbre")
            
            print("Timbre URL:", timbre_url)



            timbre_api_url = 'http://13.125.27.204:8080/users/{userId}/timbre'  # 서버주소는 애플리케이션이 실행되는 주소
            timbre_api_url = timbre_api_url.format(userId=user_id)
            params = {
                'timbre_url': timbre_url
            }

            response = requests.patch(timbre_api_url, params=params)

            # 응답 처리
            if response.status_code == 200:
                print("Timbre Update Successfully: ", response.json())

                top10_songs = predict.predict_song(mel_path, activate=False)

                print(top10_songs)

                for song_id in range(1, 11):
                    recommendations_api_url = 'http://13.125.27.204:8080/recommendations'  # 서버주소는 애플리케이션이 실행되는 주소
                    recommendation = {
                        'song_id': song_id,
                        'user_id': user_id,
                        'recommendation_method': 2,
                        'recommendation_date': '2024_05_28'
                    }

                    response = requests.post(recommendations_api_url, data=recommendation)

                    # 응답 처리
                    if response.status_code == 200:
                        print("Recommendation Update Successfully: ", response.json())
                    else:
                        print("Recommendation Update Failed: ", response.status_code)
                        return jsonify({'message': 'Recommendation upload failed'}), 400
                    
                return jsonify({'message': 'Timbre upload and recommendation successfully', 'user_id': user_id, 'recommendation': top10_songs}), 200

            else:
                print("Timbre Update Failed: ", response.status_code)
                return jsonify({'message': 'Timbre URL upload failed'}), 400
        else:
            print("Upload Failed:", response.status_code)
            return jsonify({'message': 'Timbre upload failed'}), 400
    else:
        return jsonify({'message': 'File extension not allowed'}), 400


if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
