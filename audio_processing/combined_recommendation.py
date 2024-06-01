#from . import predict_song
#from . import utility

import os
import dill
import numpy as np
import librosa
from sklearn.metrics.pairwise import cosine_similarity


def recommendation(like_song_path,
                    nb_classes=20,
                    song_folder='song_data',
                    artist_folder='artists',
                    random_states=42):
    

    # Load liked songs and all songs
    like_artist, like_spectrogram, like_song_name = load_songs_from_directory(like_song_path)
    all_artist, all_spectrogram, all_song_name = load_songs_from_directory(song_folder)

    # Find the maximum length of the spectrograms
    max_length = max(max(spec.shape[1] for spec in like_spectrogram), max(spec.shape[1] for spec in all_spectrogram))

    # Pad all spectrograms to the maximum length
    like_spectrogram = [pad_spectrogram(spec, max_length) for spec in like_spectrogram]
    all_spectrogram = [pad_spectrogram(spec, max_length) for spec in all_spectrogram]

    # Calculate similarities
    similarities = []

    for i, like_spec in enumerate(like_spectrogram):
        like_spec = normalize_spectrogram(like_spec)
        for j, all_spec in enumerate(all_spectrogram):
            all_spec = normalize_spectrogram(all_spec)
            similarity = compute_similarity(like_spec, all_spec)
            similarities.append((like_artist[i], like_song_name[i], all_artist[j], all_song_name[j], similarity))

    # Sort and get top 10 similar songs
    similarities.sort(key=lambda x: x[4], reverse=True)
    top_10_songs = similarities[:10]

    # Print the results
    for i, (like_artist, like_song, artist, song, similarity) in enumerate(top_10_songs):
        print(f"Rank {i+1}:")
        print(f"Liked Song: {like_artist} - {like_song}")
        print(f"Recommended Song: {artist} - {song}")
        print(f"Similarity: {similarity}\n")
    

    return top_10_songs


def load_songs_from_directory(directory):
    song_list = [song for song in os.listdir(directory) if not song.startswith('.')]
    artist = []
    spectrogram = []
    song_name = []

    for song in song_list:
        with open(os.path.join(directory, song), 'rb') as fp:
            loaded_song = dill.load(fp)
            artist.append(loaded_song[0])
            spectrogram.append(loaded_song[1])
            song_name.append(loaded_song[2])
    
    return artist, spectrogram, song_name


def normalize_spectrogram(spectrogram):
    return spectrogram / np.linalg.norm(spectrogram)


def compute_similarity(spectrogram1, spectrogram2):
    spectrogram1 = normalize_spectrogram(spectrogram1)
    spectrogram2 = normalize_spectrogram(spectrogram2)
    similarity = cosine_similarity(spectrogram1, spectrogram2)
    return similarity.mean()


def pad_spectrogram(spectrogram, target_length):
    if spectrogram.shape[1] < target_length:
        pad_width = target_length - spectrogram.shape[1]
        spectrogram = np.pad(spectrogram, ((0, 0), (0, pad_width)), mode='constant')
    else:
        spectrogram = spectrogram[:, :target_length]
    return spectrogram



if __name__ == '__main__':
    recommendation(like_song_path='like_sample_mel')