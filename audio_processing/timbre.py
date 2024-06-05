
import librosa
import dill
import os


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


    # Mel-Spectrogram으로 변환
    mel_path = audio_to_mel('app-user', 'timbre-test', file_path)
    
    return mel_path



if __name__ == '__main__':
    file_path = "sample_data/broadcast.wav"
    mel_path = timbre_processing(file_path)


