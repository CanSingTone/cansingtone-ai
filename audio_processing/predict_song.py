import utility
import csv
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.manifold import TSNE

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

    weights = os.path.join(save_weights_folder, str(nb_classes) +
                        '_' + str(slice_length) + '_' + str(random_states))
    
    Y_set, X_set, S_set = utility.load_dataset(song_folder_name=song_folder,
                                             artist_folder=artist_folder,
                                             nb_classes=nb_classes,
                                             random_state=random_states)
    
    X_set, Y_set, S_set = utility.slice_songs(X_set, Y_set, S_set,
                                              length=slice_length)
    
    X_set = X_set.reshape(X_set.shape + (1,))



    # Load each song into memory if the artist is included and return
    
    with open(song_path, 'rb') as fp:
        loaded_song = dill.load(fp)
    
    sample = loaded_song[1]

    # Create empty lists for train and test sets
    spectrogram = []

    slices = int(sample.shape[1] / slice_length)
    for j in range(slices - 1):
        spectrogram.append(sample[:, slice_length * j:slice_length * (j + 1)])
            
    sample = np.array(spectrogram)

    # Reshape data as 2d convolutional tensor shape
    sample = sample.reshape(sample.shape + (1,))




    # Load weights that gave best performance on validation set
    model = load_model(weights + "/")

    # 모델의 입력부터 bottleneck layer까지의 서브 모델을 만듭니다.
    bottleneck_model = Model(inputs=model.input, outputs=model.get_layer('gru_3').output)

    # 각 곡의 bottleneck layer 활성화 값을 저장할 리스트를 생성합니다.
    song_bottleneck_activations = []
    
    if activate:
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

    #data = np.array([item[2] for item in song_bottleneck_activations])

    # t-SNE 모델 인스턴스화
    #tsne = TSNE(n_components=2, random_state=42)

    # t-SNE를 사용하여 데이터를 2차원으로 축소
    #data_tsne = tsne.fit_transform(data)

    # 시각화
    #plt.figure(figsize=(10, 8))
    #plt.scatter(data_tsne[:, 0], data_tsne[:, 1])
    #plt.title('t-SNE Visualization of Song Activations')
    #plt.xlabel('t-SNE Component 1')
    #plt.ylabel('t-SNE Component 2')
    #plt.show()

    # 해당 곡의 bottleneck layer 활성화 값과 다른 곡들의 활성화 값들 간의 유사도를 계산합니다.
    similarities = {}
    for sample_id, sample_data in enumerate(sample):
        # sample prediction
        sample_data = np.expand_dims(sample_data, axis=0)
        sample_bottleneck_output = bottleneck_model.predict(sample_data)

        # 벡터로 변형
        sample_bottleneck_output = sample_bottleneck_output.reshape(-1)

        if sample_id==0:
            print(sample_bottleneck_output)

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


        similarities[sample_id] = slice_similarities

    predictions = []

    for id, data in similarities.items():
        similarities_data = np.array(data)

        similarities_idx = np.argsort(similarities_data[:, 2])
        sorted_similarities = similarities_data[similarities_idx]

        rank = []
        prediction = []

        print(f"Slice {id}")
        for i in range(-1, -20, -1):
            if float(sorted_similarities[i][2]) < 0.1:
                continue
            
            rank.append([sorted_similarities[i][0], sorted_similarities[i][1], float(sorted_similarities[i][2])])
            prediction.append(float(sorted_similarities[i][2]))

            if len(rank) >= 10:
                break
        
        predictions.append(prediction)

        for i in range(10):
            print(f"{i}번째로 높은 유사도의 가수, 노래, 유사도: ", rank[i][0], rank[i][1], rank[i][2])
    
    predictions = np.array(predictions)

    print(predictions)

    # 히트맵 그리기
    #plt.imshow(predictions, cmap='hot', interpolation='nearest')
    #plt.colorbar()  # 컬러바 추가
    #plt.show()



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
    #with open(file_path, 'w', newline='') as file:
    #    writer = csv.writer(file)
    #    for activation in activations:
    #        writer.writerow(activation)

    # 데이터를 DataFrame으로 변환
    df = pd.DataFrame(activations, columns=['artist', 'song', 'activation'])

    df['activation'] = df['activation'].apply(lambda x: ' '.join(map(str, x)))

    # 데이터를 CSV 파일로 저장
    df.to_csv(file_path, index=False)


def load_activations_from_file(file_path="activations.csv"):
    #activations = []
    #with open(file_path, 'r', newline='') as file:
    #    reader = csv.reader(file)
    #    for row in reader:
    #        activations.append(row)

    
    # CSV 파일에서 데이터 불러오기
    loaded_df = pd.read_csv(file_path)

    # '활성 값' 열의 값들을 다시 numpy 배열로 변환
    loaded_df['activation'] = loaded_df['activation'].apply(lambda x: np.array([float(val) for val in x.split()]))

    return loaded_df.values


if __name__ == '__main__':
    predict_song('sample_mel/ben_%%-%%_꿈처럼vocal.mp3', activate=False)