import librosa
import os
import numpy as np

# 오디오 파일 로드
sample_folder = "sample_data"
audio_file = "테스트.mp3"
sample_path = os.path.join(sample_folder, audio_file)
y, sr = librosa.load(sample_path)
"""
# 주파수 스펙트럼 분석
D = librosa.stft(y)
mag = librosa.amplitude_to_db(abs(D))

# 주파수를 음정으로 변환
pitch, _ = librosa.core.piptrack(y=y, sr=sr)

# 최고 음과 최저 음 계산
max_pitch = librosa.hz_to_midi(pitch.max())
min_pitch = librosa.hz_to_midi(pitch.min())

print("최고 음:", max_pitch)
print("최저 음:", min_pitch)
"""

# 주파수 스펙트럼 분석
D = librosa.stft(y)
mag, phase = librosa.magphase(D)

# 주파수를 음정으로 변환
pitches, magnitudes = librosa.core.piptrack(S=mag, sr=sr)

# 최고 음과 최저 음 계산
pitch_values = pitches[magnitudes > np.median(magnitudes)]

# 임계점 설정 (예: 5000 Hz 이상 주파수 무시)
#threshold_hz = 500

# 임계점 이하의 주파수 값만 고려하여 최고 음 구하기
#pitch_values = pitches[(magnitudes > np.median(magnitudes)) & (pitches < threshold_hz)]

max_pitch_hz = pitch_values.max()
min_pitch_hz = pitch_values.min()

# Hz를 음정으로 변환
max_pitch_midi = librosa.hz_to_midi(max_pitch_hz)
min_pitch_midi = librosa.hz_to_midi(min_pitch_hz)

# MIDI 음계를 음정 이름으로 변환
max_pitch_note = librosa.midi_to_note(max_pitch_midi)
min_pitch_note = librosa.midi_to_note(min_pitch_midi)

print("최고 음:", max_pitch_note)
print("최저 음:", min_pitch_note)
