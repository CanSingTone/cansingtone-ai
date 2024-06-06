import os
import dill

length = 628

# Paths (adjust as needed)
artist_folder = 'artists'
song_folder_name = 'song_data'
save_folder = 'song_data_temp'
os.makedirs(save_folder, exist_ok=True)

# Get all songs saved as numpy arrays in the given folder
song_list = [song for song in os.listdir(song_folder_name) if not song.startswith('.')]

# Get list of all artists
artists = [path for path in os.listdir(artist_folder) if os.path.isdir(os.path.join(artist_folder, path))]

# Create empty lists
artist = []
spectrogram = []
song_name = []
song_id = []

for song in song_list:
    with open(os.path.join(song_folder_name, song), 'rb') as fp:
        loaded_song = dill.load(fp)
    if loaded_song[0] in artists:
        artist.append(loaded_song[0])
        spectrogram.append(loaded_song[1])
        song_name.append(loaded_song[2])
        song_id.append(loaded_song[3])

artist_sliced = []
spectrogram_sliced = []
song_name_sliced = []
song_id_sliced = []

for i, song in enumerate(spectrogram):
    # Slice the log_S into 20-second chunks
    slices = int(song.shape[1] / length)
    for j in range(slices):
        spectrogram_sliced.append(song[:, length * j:length * (j + 1)])
        artist_sliced.append(artist[i])
        song_name_sliced.append(song_name[i])
        song_id_sliced.append(song_id[i])

        if j == slices - 1:
            spectrogram_sliced.append(song[:, length * (j+1):])
            artist_sliced.append(artist[i])
            song_name_sliced.append(song_name[i])
            song_id_sliced.append(song_id[i])

idx = 0
pre_id = song_id_sliced[0]

for i, song in enumerate(spectrogram_sliced):
    if pre_id != song_id_sliced[i]:
        idx = 0

    data = (artist_sliced[i], song, song_name_sliced[i], song_id_sliced[i])  # Adding slice index
    # Save each slice
    save_name = f"{artist_sliced[i]}_%%-%%_{song_name_sliced[i]}_%%-%%_{song_id_sliced[i]}_%%-%%_{idx}.mp3"
    with open(os.path.join(save_folder, save_name), 'wb') as fp:
        dill.dump(data, fp)

    pre_id = song_id_sliced[i]
    idx += 1

