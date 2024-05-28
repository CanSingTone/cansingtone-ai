from flask import Flask, request, jsonify
import requests
import os

import audio_processing.pitch as pitch

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
            print("Update Successfully")
            print("response data:", response.json())
        else:
            print("Update Failed:", response.status_code, response.text)
        
        # 분석 결과 반환
        return jsonify({'message': 'File uploaded successfully', 'highest_note': highest_note, 'lowest_note': lowest_note, 'user_id': user_id}), 200
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

        return jsonify({'message': 'File URL Upload successfully', 'file_name': file.filename, 'user_id': user_id}), 200

        # 파일 저장
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # 파일 경로를 pitch_processing 함수에 전달하여 분석
        # = pitch.pitch_processing(os.path.join(app.config['UPLOAD_FOLDER'], filename))



        url = 'http://13.125.27.204:8080/upload'  # 서버주소는 애플리케이션이 실행되는 주소
        params = {
            'file': file,
        }

        response = requests.patch(url, params=params)

        url = 'http://13.125.27.204:8080/users/{userId}/timbre'  # 서버주소는 애플리케이션이 실행되는 주소
        full_url = url.format(userId=user_id)
        params = {
            'timbre_url': timbre_url,
        }

        response = requests.patch(full_url, params=params)

        # 응답 처리
        if response.status_code == 200:
            print("File URL Upload Successfully")
            print("response data:", response.json())
        else:
            print("File URL Upload Failed:", response.status_code, response.text)
        
        # 분석 결과 반환
        return jsonify({'message': 'File URL Upload successfully', 'timbre_url': timbre_url, 'user_id': user_id}), 200
    else:
        return jsonify({'message': 'File extension not allowed'}), 400


if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
