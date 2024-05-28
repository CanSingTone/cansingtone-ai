from . import predict_song

import requests
import librosa
import dill
import os
import numpy as np

def auto_vad():
    return


def audio_to_mel(artist, song, file_path, save_folder='sample_mel', sr=16000, n_mels=128,
                   n_fft=2048, hop_length=512):
    
    # Create mel spectrogram and convert it to the log scale
    y, sr = librosa.load(file_path, sr=sr)
    S = librosa.feature.melspectrogram(y, sr=sr, n_mels=n_mels,
                                        n_fft=n_fft,
                                        hop_length=hop_length)
    log_S = librosa.power_to_db(S, ref=1.0)
    data = (artist, log_S, song)

    # Save each song
    save_name = artist + "_" + song + ".mp3"
    mel_path = os.path.join(save_folder, save_name)
    with open(mel_path, 'wb') as fp:
        dill.dump(data, fp)

    return mel_path


def timbre_processing(file_path):
    # 녹음 파일이 들어오면 가창 등장 부분 거르고 mel 변환
    # 최종적으로 mel spectrogram 파일이 될 것이다 이거를 db에 저장할 거임
    # 이거 가지고 추천 작업 시작
    # 슬라이스 뭐 이미 있는 곡들의 값들과 비교 네트워크 통과 등등 유사도 통해서 상위 10곡 반환

    # 가창 부분 추출하는 코드 추가 필요


    # Mel-Spectrogram으로 변환
    mel_path = audio_to_mel('app-user', 'timbre-test', file_path)
    
    return mel_path


if __name__ == '__main__':
    file_path = "sample_data/1_1_1_벤_꿈처럼_(Vocals)_(Vocals)_(No Reverb).mp3"
    mel_path = timbre_processing(file_path)

    test = True

    if test:
        user_id = '4'

        s3_url = 'http://13.125.27.204:8080/upload'
        files = {'file': open(mel_path, 'rb')}

        response = requests.post(s3_url, files=files)

        # 응답 처리
        if response.status_code == 200:
            print("Timbre File Upload Successfully: ", response.json())
            
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
            else:
                print("Timbre Update Failed: ", response.status_code)
        else:
            print("Timbre Upload Failed: ", response.status_code)

        
        top10_songs = predict_song.predict_song(mel_path, activate=False)

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



        