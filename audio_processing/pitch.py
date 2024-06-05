import os
import shutil
import mido
import pandas as pd

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

import requests

def midi_to_note_name(midi_note):
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = midi_note // 12 - 1
    note = note_names[midi_note % 12]
    return f"{note}{octave}"


def mp3_to_mid(mp3_file_path):
    # MP3 파일 경로와 다운로드 받을 위치
    download_dir = "./sample_midi"

    # sample_midi 디렉토리가 존재하는지 확인한 후, 존재하면 삭제
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)

    # sample_midi 디렉토리를 새로 생성
    os.makedirs(download_dir)
    download_dir_absolute = os.path.abspath(download_dir)

    # 브라우저 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 헤드리스 모드
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir_absolute,  # 다운로드 디렉토리 설정
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    # ChromeDriverManager 설치 경로 가져오기 및 Service 객체 생성
    service = Service(ChromeDriverManager().install())

    # 웹드라이버 초기화
    driver = webdriver.Chrome(service=service, options=options)

    midi_file = 'basic_pitch_transcription.mid'

    try:
        # 웹사이트 열기
        driver.get("https://basicpitch.spotify.com/")

        # 파일 드래그 앤 드랍 영역 또는 클릭 영역 찾기
        drop_area = WebDriverWait(driver, 90).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )

        # 파일 입력 요소에 파일 경로 설정
        mp3_file_path_absolute = os.path.abspath(mp3_file_path)
        driver.execute_script("arguments[0].style.display = 'block';", drop_area)
        drop_area.send_keys(mp3_file_path_absolute)

        # 다운로드 버튼 클릭
        download_button = WebDriverWait(driver, 240).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Download Midi')]"))
        )
        download_button.click()

        # 다운로드 완료 대기 (적절한 시간으로 설정)
        time.sleep(5)
    except:
        midi_file = 'dummy'
    finally:
        # 브라우저 종료
        driver.quit()

    midi_path = os.path.join(download_dir, midi_file)

    if os.path.exists(midi_path):
        return midi_path
    else:
        return None


def pitch_processing(file_path):
    if file_path[-3:].lower() in ['mp3', 'aac']:
        file_path = mp3_to_mid(file_path)
    else:
        print("잘못된 파일 형식")
        return -1, -1
    
    if file_path == None:
        print("접속 실패")
        return -1, -1

    midi = mido.MidiFile(file_path)

    # 노이즈로 간주되는 노트 제거 (예: 매우 짧은 노트 등)
    # 사용X 참고용
    cleaned_tracks = []
    for track in midi.tracks:
        new_track = mido.MidiTrack()
        for msg in track:
            # 예시: 노트 길이가 짧은 경우 노이즈로 간주
            if msg.type == 'note_on' and msg.velocity > 0 and msg.time > -1:
                new_track.append(msg)
        cleaned_tracks.append(new_track)

    new_midi = mido.MidiFile()
    for track in cleaned_tracks:
        new_midi.tracks.append(track)

    # 모든 노트 이벤트에서 피치 정보 추출
    pitches = []
    threshold = 80
    #print(f"threshold: {threshold}")

    for i, track in enumerate(midi.tracks):
        for msg in track:
            if msg.type == 'note_on' and msg.velocity > threshold:
                pitches.append(msg.note)

    if pitches:
        # 최고 음과 최저 음 계산
        max_pitch = max(pitches)
        min_pitch = min(pitches)

        # MIDI 값을 음정 이름으로 변환
        max_pitch_note = midi_to_note_name(max_pitch)
        min_pitch_note = midi_to_note_name(min_pitch)

        print(f"최고 음 (MIDI): {max_pitch} -> 음정: {max_pitch_note}")
        print(f"최저 음 (MIDI): {min_pitch} -> 음정: {min_pitch_note}")
    else:
        max_pitch = -1
        min_pitch = -1

        print("최고음과 최저음을 찾을 수 없습니다.")

    return max_pitch, min_pitch


def read_csv_data(csv_file):
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    return df
    

def update_csv_with_pitch_data(csv_file, downloads_folder, batch_size=10):    
    df = read_csv_data(csv_file)
    
    # Adding columns for highest_note and lowest_note if not present
    if 'highest_note80' not in df.columns:
        df['highest_note80'] = None
    if 'lowest_note80' not in df.columns:
        df['lowest_note80'] = None

    processed_count = 0

    for file_name in os.listdir(downloads_folder):
        if file_name.endswith('.mp3'):
            artist, song_title, song_id = file_name[:-4].split("__")

            print(f"테스트 곡: {artist} - {song_title}.mp3")
            
            file_path = os.path.join(downloads_folder, file_name)
            highest_note, lowest_note = pitch_processing(file_path)
            
            # Update the CSV dataframe
            mask = df['index'] == int(song_id)
            df.loc[mask, 'highest_note80'] = highest_note
            df.loc[mask, 'lowest_note80'] = lowest_note

            processed_count += 1

            # Save progress after processing each batch
            if processed_count % batch_size == 0:
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                print(f"Processed {processed_count} files and saved progress to CSV.")
    
    # Save the updated dataframe back to CSV
    #df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    #print(f"Updated CSV file: {csv_file}")


if __name__ == '__main__':
    
    api_test = False
    csv_test = True

    if api_test:
        file_path = "sample_data/test.mp3"
        highest_note, lowest_note = pitch_processing(file_path)

        user_id = '4'

        url = 'http://13.125.27.204:8080/users/{userId}/vocal-range'  # 서버주소는 애플리케이션이 실행되는 주소
        full_url = url.format(userId=user_id)
        params = {
            'vocal_range_high': highest_note,
            'vocal_range_low': lowest_note
        }

        response = requests.patch(full_url, params=params)

        # 응답 처리
        if response.status_code == 200:
            print("Pitch Update Successfully: ", response)
        else:
            print("Pitch Update Failed:", response)

    if csv_test:
        # 파일 경로와 폴더 경로 설정
        csv_file = 'song_copy.csv'
        downloads_folder = 'sample_vad'

        # 업데이트 작업 수행
        update_csv_with_pitch_data(csv_file, downloads_folder)


