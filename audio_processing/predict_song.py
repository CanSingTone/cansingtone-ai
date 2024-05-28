import utility
import pandas as pd
import dill
import os
import numpy as np

from tensorflow.keras.models import load_model
from keras.models import Model


def predict_song(song_path,
                    nb_classes=20,
                    slice_length=911,
                    activate=True,
                    csv_file_path='activations.csv',
                    song_folder='song_data',
                    save_weights_folder='weights_song_split',
                    artist_folder='artists',
                    random_states=42):
    """
    Main function for training the model and testing
    """

    # Load each song into memory if the artist is included and return
    with open(song_path, 'rb') as fp:
        loaded_song = dill.load(fp)
    
    sample = loaded_song[1]

    # Create empty lists for train and test sets
    spectrogram = []

    slices = int(sample.shape[1] / slice_length)
    for j in range(slices):
        spectrogram.append(sample[:, slice_length * j:slice_length * (j + 1)])
            
    sample = np.array(spectrogram)

    # Reshape data as 2d convolutional tensor shape
    sample = sample.reshape(sample.shape + (1,))



    # Load weights that gave best performance on validation set
    weights = os.path.join(save_weights_folder, str(nb_classes) +
                        '_' + str(slice_length) + '_' + str(random_states))
    model = load_model(weights + "/")


    # 모델의 입력부터 bottleneck layer까지의 서브 모델을 만듭니다.
    bottleneck_model = Model(inputs=model.input, outputs=model.get_layer('gru_3').output)

    # 각 곡의 bottleneck layer 활성화 값을 저장할 리스트를 생성합니다.
    song_bottleneck_activations = []
    
    if activate:
        Y_set, X_set, S_set = utility.load_dataset(song_folder_name=song_folder,
                                             artist_folder=artist_folder,
                                             nb_classes=nb_classes,
                                             random_state=random_states)
    
        X_set, Y_set, S_set = utility.slice_songs(X_set, Y_set, S_set,
                                                length=slice_length)
        
        X_set = X_set.reshape(X_set.shape + (1,))

        # 모든 곡에 대해 bottleneck layer의 활성화 값을 추출
        for id, song_data in enumerate(X_set):
            # 차원 맞추기
            song_data = np.expand_dims(X_set[id], axis=0)
            # bottleneck layer의 출력
            song_bottleneck_output = bottleneck_model.predict(song_data)
            song_bottleneck_output = song_bottleneck_output.reshape(-1)
            # 해당 곡의 bottleneck layer 활성화 값을 가수명, 곡명과 함께 리스트에 저장
            song_bottleneck_activations.append([Y_set[id], S_set[id], song_bottleneck_output])

        save_activations_to_file(song_bottleneck_activations, csv_file_path)
    else:
        song_bottleneck_activations = load_activations_from_file(csv_file_path)



    # 해당 곡의 bottleneck layer 활성화 값과 다른 곡들의 활성화 값들 간의 유사도를 계산합니다.
    similarities = {}
    aggregated_similarities = {}
    for sample_id, sample_data in enumerate(sample):
        # sample prediction
        sample_data = np.expand_dims(sample_data, axis=0)
        sample_bottleneck_output = bottleneck_model.predict(sample_data)

        # 벡터로 변형
        sample_bottleneck_output = sample_bottleneck_output.reshape(-1)

        #print(sample_bottleneck_output.shape, sample_bottleneck_output)

        flag = True
        # calculating simularity
        slice_similarities = []
        for artist, song, song_data in song_bottleneck_activations:    
            #print(song_data.shape, song_data)
            #similarity = np.dot(sample_bottleneck_output, song_data)
            similarity = cosine_similarity(sample_bottleneck_output, song_data)
            #similarity = np.dot(normalize_vector(sample_bottleneck_output), normalize_vector(song_data))
            slice_similarities.append([artist, song, similarity])

        
        # slice_similarities 리스트를 DataFrame으로 변환
        df = pd.DataFrame(slice_similarities, columns=['artist', 'song', 'similarity'])

        # 곡 단위로 유사도 합산
        song_similarities = df.groupby(['artist', 'song'])['similarity'].mean().reset_index()

        for _, row in song_similarities.iterrows():
            artist, song, similarity = row['artist'], row['song'], row['similarity']
            if (artist, song) not in aggregated_similarities:
                aggregated_similarities[(artist, song)] = 0
            aggregated_similarities[(artist, song)] += similarity

        similarities[sample_id] = slice_similarities

    for key, value in aggregated_similarities.items():
        aggregated_similarities[key] = value / slices

    top_10_similarities = sorted(aggregated_similarities.items(), key=lambda x: x[1], reverse=True)[:10]

    print(top_10_similarities)

    return top_10_similarities


def cosine_similarity(vector1, vector2):
    dot_product = np.dot(vector1, vector2)
    norm1 = np.linalg.norm(vector1)
    norm2 = np.linalg.norm(vector2)
    similarity = dot_product / (norm1 * norm2)
    return similarity


def normalize_vector(vector):
    norm = np.linalg.norm(vector)
    normalized_vector = vector / norm
    return normalized_vector


def save_activations_to_file(activations, file_path="activations.csv"):
    # 데이터를 DataFrame으로 변환
    df = pd.DataFrame(activations, columns=['artist', 'song', 'activation'])

    df['activation'] = df['activation'].apply(lambda x: ' '.join(map(str, x)))

    # 데이터를 CSV 파일로 저장
    df.to_csv(file_path, index=False)


def load_activations_from_file(file_path="activations.csv"):
    # CSV 파일에서 데이터 불러오기
    loaded_df = pd.read_csv(file_path)

    # '활성 값' 열의 값들을 다시 numpy 배열로 변환
    loaded_df['activation'] = loaded_df['activation'].apply(lambda x: np.array([float(val) for val in x.split()]))

    return loaded_df.values


if __name__ == '__main__':
    predict_song('sample_mel/app-user_timbre-test1.0.mp3', activate=False)