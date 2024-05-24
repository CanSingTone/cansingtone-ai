from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename

from audio_processing import pitch

app = Flask(__name__)

@app.route('/',methods=['GET'])
def test():
    return "hello flask"

# 허용할 파일 확장자
ALLOWED_EXTENSIONS = {'mp3', 'acc'}

# 업로드된 파일이 허용된 확장자인지 확인하는 함수
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# mp3 파일을 받는 엔드포인트
@app.route('/upload-mp3', methods=['POST'])
def upload_mp3():
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
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # 파일 경로를 pitch_processing 함수에 전달하여 분석
        highest_note, lowest_note = pitch.pitch_processing(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # 분석 결과 반환
        return jsonify({'message': 'File uploaded successfully', 'highest_note': highest_note, 'lowest_note': lowest_note, 'user_id': user_id}), 200
    else:
        return jsonify({'message': 'File extension not allowed'}), 400

if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
