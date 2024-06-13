from . import utility
import pandas as pd
import dill
import os
import numpy as np
import random

from keras.models import load_model
from keras.models import Model


def predict_song(song_path,
                    nb_classes=228,
                    slice_length=313,
                    activate=True,
                    csv_file_path='activations.csv',
                    song_folder='song_data',
                    save_weights_folder='weights_song_split',
                    artist_folder='artists',
                    random_states=0):
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
    bottleneck_model = Model(inputs=model.input, outputs=model.get_layer('dense_4').output)

    # 각 곡의 bottleneck layer 활성화 값을 저장할 리스트를 생성합니다.
    song_bottleneck_activations = []
    
    if activate:
        Y_set, X_set, S_set, I_set = utility.load_dataset(song_folder_name=song_folder,
                                             artist_folder=artist_folder,
                                             nb_classes=nb_classes,
                                             random_state=random_states)
    
        X_set, Y_set, S_set, I_set = utility.slice_songs(X_set, Y_set, S_set, I_set,
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
            song_bottleneck_activations.append([Y_set[id], S_set[id], I_set[id], song_bottleneck_output])

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
        for artist, song, song_id, song_data in song_bottleneck_activations:    
            #print(song_data.shape, song_data)
            #similarity = np.dot(sample_bottleneck_output, song_data)
            similarity = cosine_similarity(sample_bottleneck_output, song_data)
            #similarity = np.dot(normalize_vector(sample_bottleneck_output), normalize_vector(song_data))
            slice_similarities.append([artist, song, song_id, similarity])

        
        # slice_similarities 리스트를 DataFrame으로 변환
        df = pd.DataFrame(slice_similarities, columns=['artist', 'song', 'song_id', 'similarity'])

        # 곡 단위로 유사도 합산
        song_similarities = df.groupby(['artist', 'song', 'song_id'])['similarity'].mean().reset_index()

        for _, row in song_similarities.iterrows():
            artist, song, song_id, similarity = row['artist'], row['song'], row['song_id'], row['similarity']
            if (artist, song, song_id) not in aggregated_similarities:
                aggregated_similarities[(artist, song, song_id)] = 0
            aggregated_similarities[(artist, song, song_id)] += similarity

        similarities[sample_id] = slice_similarities

    for key, value in aggregated_similarities.items():
        aggregated_similarities[key] = value / slices

    # Step 1: 유사도 값으로 정렬
    sorted_similarities = sorted(aggregated_similarities.items(), key=lambda x: x[1], reverse=True)

    top_30_similarities = sorted_similarities[:30]

    print("top_30_similarities: ", top_30_similarities)

    return sorted_similarities

    # Step 2: 유사도가 0.5를 넘는 항목들 필터링
    over_80 = [item for item in sorted_similarities if item[1] > 0.8]
    over_75 = [item for item in sorted_similarities if item[1] > 0.75]
    over_70 = [item for item in sorted_similarities if item[1] > 0.7]
    over_65 = [item for item in sorted_similarities if item[1] > 0.65]
    over_60 = [item for item in sorted_similarities if item[1] > 0.6]

    # Step 3: 조건에 따라 랜덤 샘플 선택
    if len(over_80) >= 10:
        indices = sorted(random.sample(range(len(over_80)), 10))
    elif len(over_75) >= 10:
        indices = sorted(random.sample(range(len(over_75)), 10))
    elif len(over_70) >= 10:
        indices = sorted(random.sample(range(len(over_70)), 10))
    elif len(over_65) >= 10:
        indices = sorted(random.sample(range(len(over_65)), 10))
    elif len(over_60) >= 10:
        indices = sorted(random.sample(range(len(over_60)), 10))
    else:
        # 50개 미만인 경우 상위 30개에서 랜덤한 10개 선택
        indices = sorted(random.sample(range(15), 10))

    # Step 4: 랜덤 샘플에서 (artist, song, song_id)만 추출
    #random_10_items = [item[0] for item in random_samples]
    random_10_items = [sorted_similarities[i] for i in indices]

    print(random_10_items)

    top_30_similarities = sorted(aggregated_similarities.items(), key=lambda x: x[1], reverse=True)[:30]

    print("top_30_similarities: ", top_30_similarities)

    return random_10_items


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
    df = pd.DataFrame(activations, columns=['artist', 'song', 'song_id', 'activation'])

    df['activation'] = df['activation'].apply(lambda x: ' '.join(map(str, x)))

    # 데이터를 CSV 파일로 저장
    df.to_csv(file_path, index=False, encoding='utf-8-sig')


def load_activations_from_file(file_path="activations.csv"):
    # CSV 파일에서 데이터 불러오기
    loaded_df = pd.read_csv(file_path, encoding='utf-8-sig')

    # '활성 값' 열의 값들을 다시 numpy 배열로 변환
    loaded_df['activation'] = loaded_df['activation'].apply(lambda x: np.array([float(val) for val in x.split()]))

    return loaded_df.values


if __name__ == '__main__':
    nb_classes = 232
    slice_length = 157
    random_states = 21
    csv_file = f"activations_{nb_classes}_{slice_length}_{random_states}.csv"
    song_folder = "song_data_male"
    artists = "artists_male_name"
    predict_song('song_data_male/태진아_%%-%%_미안 미안해_%%-%%_1983.mp3', 
                activate=False, 
                slice_length=slice_length, 
                nb_classes=nb_classes, 
                random_states=random_states, 
                csv_file_path=csv_file,
                song_folder=song_folder,
                artist_folder=artists)