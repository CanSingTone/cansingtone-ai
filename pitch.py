import librosa
import os
import numpy as np
import mido


def midi_to_note_name(midi_note):
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = midi_note // 12 - 1
    note = note_names[midi_note % 12]
    return f"{note}{octave}"


def mp3_to_mid(mp3_file_path):
    mid_file_path = mp3_file_path
    return mid_file_path


def pitch_processing(file_path):
    mid_file = mp3_to_mid(file_path)
    midi = mido.MidiFile(mid_file)

    # 노이즈로 간주되는 노트 제거 (예: 매우 짧은 노트 등)
    cleaned_tracks = []
    for track in midi.tracks:
        new_track = mido.MidiTrack()
        for msg in track:
            # 예시: 노트 길이가 짧은 경우 노이즈로 간주
            if msg.type == 'note_on' and msg.velocity > 0 and msg.time > 5:
                new_track.append(msg)
        cleaned_tracks.append(new_track)

    new_midi = mido.MidiFile()
    for track in cleaned_tracks:
        new_midi.tracks.append(track)

    # 모든 노트 이벤트에서 피치 정보 추출
    pitches = []
    threshold = 52
    print(f"threshold: {threshold}")

    for i, track in enumerate(new_midi.tracks):
        for msg in track:
            if msg.type == 'note_on' and msg.velocity > threshold:
                pitches.append(msg.note)

    # 최고 음과 최저 음 계산
    max_pitch = max(pitches)
    min_pitch = min(pitches)

    # MIDI 값을 음정 이름으로 변환
    max_pitch_note = midi_to_note_name(max_pitch)
    min_pitch_note = midi_to_note_name(min_pitch)

    print(f"최고 음 (MIDI): {max_pitch} -> 음정: {max_pitch_note}")
    print(f"최저 음 (MIDI): {min_pitch} -> 음정: {min_pitch_note}")



"""
# 오디오 파일 로드
sample_folder = "sample_data"
audio_file = "벤_꿈처럼_gaudiolab_vocal_stretch.mp3"
sample_path = os.path.join(sample_folder, audio_file)
y, sr = librosa.load(sample_path)


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

"""







