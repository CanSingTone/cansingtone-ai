import os
import dill

import numpy as np
from numpy.random import RandomState

import librosa
import librosa.display


def create_dataset(artist_folder='artists', save_folder='song_data',
                   sr=16000, n_mels=128,
                   n_fft=2048, hop_length=512):
    """This function creates the dataset given a folder
     with the correct structure (artist_folder/artists/albums/*.mp3)
    and saves it to a specified folder."""

    # get list of all artists
    os.makedirs(save_folder, exist_ok=True)
    artists = [path for path in os.listdir(artist_folder) if os.path.isdir(os.path.join(artist_folder, path))]

    # iterate through all artists, albums, songs and find mel spectrogram
    for artist in artists:
        print(artist)
        artist_path = os.path.join(artist_folder, artist)
        artist_songs = [song for song in os.listdir(artist_path) if not song.startswith('.')]

        for song in artist_songs:
            song_path = os.path.join(artist_path, song)

            _, song, song_id = song[:-4].split("__")

            # Create mel spectrogram and convert it to the log scale
            y, sr = librosa.load(song_path, sr=sr)
            S = librosa.feature.melspectrogram(y, sr=sr, n_mels=n_mels,
                                                n_fft=n_fft,
                                                hop_length=hop_length)
            log_S = librosa.power_to_db(S, ref=np.max)
            data = (artist, log_S, song, song_id)

            # Save each song
            save_name = artist + '_%%-%%_' + song + '_%%-%%_' + song_id + '.mp3'
            with open(os.path.join(save_folder, save_name), 'wb') as fp:
                dill.dump(data, fp)


def load_dataset(song_folder_name='song_data',
                 artist_folder='artists',
                 nb_classes=20, random_state=42):
    """This function loads the dataset based on a location;
     it returns a list of spectrograms
     and their corresponding artists/song names"""

    # Get all songs saved as numpy arrays in the given folder
    song_list = [song for song in os.listdir(song_folder_name) if not song.startswith('.')]
    
    # Load the list of artists
    artist_list = [path for path in os.listdir(artist_folder) if os.path.isdir(os.path.join(artist_folder, path))]

    # select the appropriate number of classes
    prng = RandomState(random_state)
    artists = prng.choice(artist_list, size=nb_classes, replace=False)

    # Create empty lists
    artist = []
    spectrogram = []
    song_name = []
    song_id = []

    # Load each song into memory if the artist is included and return
    for song in song_list:
        with open(os.path.join(song_folder_name, song), 'rb') as fp:
            loaded_song = dill.load(fp)
        if loaded_song[0] in artists:
            artist.append(loaded_song[0])
            spectrogram.append(loaded_song[1])
            song_name.append(loaded_song[2])
            song_id.append(loaded_song[3])

    return artist, spectrogram, song_name, song_id


def slice_songs(X, Y, S, I, length=911):
    """Slices the spectrogram into sub-spectrograms according to length"""

    # Create empty lists for train and test sets
    artist = []
    spectrogram = []
    song_name = []
    song_id = []

    # Slice up songs using the length specified
    for i, song in enumerate(X):
        slices = int(song.shape[1] / length)
        for j in range(slices):
            spectrogram.append(song[:, length * j:length * (j + 1)])
            artist.append(Y[i])
            song_name.append(S[i])
            song_id.append(I[i])

    return np.array(spectrogram), np.array(artist), np.array(song_name), np.array(song_id)


if __name__ == '__main__':

    # configuration options
    create_data = True

    if create_data:
        create_dataset(artist_folder='artists', save_folder='song_data',
                       sr=16000, n_mels=128, n_fft=2048,
                       hop_length=512)
