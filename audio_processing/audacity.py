import pyaudacity as pa
import os
import time


def execute_audacity_command(command):
    """
    Execute an Audacity command and check if it was successful.
    """
    response = pa.do(command)
    if "OK" not in response:
        raise Exception(f"Command failed: {command}\nResponse: {response}")
    return response

input_path = 'output'
output_path = 'output_vad'

songs = [path for path in os.listdir(input_path) if not path.startswith('.')]

for song in songs:
    input_name = song
    input_song_path = os.path.join(input_path, input_name)
    output_name = song[:-4] + " pyaudacity.mp3"
    output_song_path = os.path.join(output_path, output_name)

    input_path_absolute = os.path.abspath(input_song_path)
    output_path_absolute = os.path.abspath(output_song_path)

    try:
        execute_audacity_command(f'Import2: Filename="{input_path_absolute}"')
        time.sleep(1)
        execute_audacity_command('SelAllTracks')
        time.sleep(1)
        execute_audacity_command('Amplify: Ratio="15"')
        time.sleep(1)
        execute_audacity_command('TruncateSilence')
        time.sleep(1)
        execute_audacity_command('Amplify: Ratio="0.075"')
        time.sleep(1)
        execute_audacity_command(f'Export2: Filename="{output_path_absolute}"')

    except Exception as e:
        print(f"An error occurred: {e}")