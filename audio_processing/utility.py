import os
import dill

import numpy as np
from numpy.random import RandomState

import librosa
import librosa.display

from sklearn.model_selection import train_test_split


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
        artist_albums = [path for path in os.listdir(artist_path) if os.path.isdir(os.path.join(artist_path, path))]

        for album in artist_albums:
            album_path = os.path.join(artist_path, album)
            album_songs = [song for song in os.listdir(album_path) if not song.startswith('.')]

            for song in album_songs:
                song_path = os.path.join(album_path, song)

                # Create mel spectrogram and convert it to the log scale
                y, sr = librosa.load(song_path, sr=sr)
                S = librosa.feature.melspectrogram(y, sr=sr, n_mels=n_mels,
                                                   n_fft=n_fft,
                                                   hop_length=hop_length)
                log_S = librosa.power_to_db(S, ref=np.max)
                data = (artist, log_S, song)

                # Save each song
                save_name = artist + '_%%-%%_' + album + '_%%-%%_' + song
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

    # Load each song into memory if the artist is included and return
    for song in song_list:
        with open(os.path.join(song_folder_name, song), 'rb') as fp:
            loaded_song = dill.load(fp)
        if loaded_song[0] in artists:
            artist.append(loaded_song[0])
            spectrogram.append(loaded_song[1])
            song_name.append(loaded_song[2])

    return artist, spectrogram, song_name


def load_dataset_song_split(song_folder_name='song_data',
                            artist_folder='artists',
                            nb_classes=20,
                            test_split_size=0.1,
                            validation_split_size=0.1,
                            random_state=42):
                            
    Y, X, S = load_dataset(song_folder_name=song_folder_name,
                           artist_folder=artist_folder,
                           nb_classes=nb_classes,
                           random_state=random_state)
    # train and test split
    X_train, X_test, Y_train, Y_test, S_train, S_test = train_test_split(
        X, Y, S, test_size=test_split_size, stratify=Y,
        random_state=random_state)

    # Create a validation to be used to track progress
    X_train, X_val, Y_train, Y_val, S_train, S_val = train_test_split(
        X_train, Y_train, S_train, test_size=validation_split_size,
        shuffle=True, stratify=Y_train, random_state=random_state)

    return Y_train, X_train, S_train, \
           Y_test, X_test, S_test, \
           Y_val, X_val, S_val


def slice_songs(X, Y, S, length=911):
    """Slices the spectrogram into sub-spectrograms according to length"""

    # Create empty lists for train and test sets
    artist = []
    spectrogram = []
    song_name = []

    # Slice up songs using the length specified
    for i, song in enumerate(X):
        slices = int(song.shape[1] / length)
        for j in range(slices - 1):
            spectrogram.append(song[:, length * j:length * (j + 1)])
            artist.append(Y[i])
            song_name.append(S[i])

    return np.array(spectrogram), np.array(artist), np.array(song_name)


if __name__ == '__main__':

    # configuration options
    create_data = True
    create_visuals = False
    save_visuals = False

    if create_data:
        create_dataset(artist_folder='artists', save_folder='song_data',
                       sr=16000, n_mels=128, n_fft=2048,
                       hop_length=512)
