from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
import numpy as np
from load_custom_data import load_custom_data  # 追加した手書きデータのロード用
from tensorflow.keras.datasets import mnist

# カスタムデータのロード
data_dir = 'static/saved_images'
custom_images, custom_labels = load_custom_data(data_dir)
print(f"{len(custom_images)} 枚の画像と対応するラベルを読み込みました。")

# MNISTデータセットのロード（既存のデータと組み合わせる）
(train_images_mnist, train_labels_mnist), _ = mnist.load_data()
train_images_mnist = train_images_mnist.reshape(-1, 28, 28, 1) / 255.0  # 正規化

# 追加データと既存データを組み合わせる
train_images, val_images, train_labels, val_labels = train_test_split(
    np.concatenate([custom_images, train_images_mnist[:1000]], axis=0),
    np.concatenate([custom_labels, train_labels_mnist[:1000]], axis=0),
    test_size=0.2,
    random_state=42
)

# モデルの定義
model = Sequential([
    Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(28, 28, 1)),
    MaxPooling2D(pool_size=(2, 2)),
    Dropout(0.25),  # 過学習防止
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),  # 過学習防止
    Dense(10, activation='softmax')
])

# モデルのコンパイル
model.compile(optimizer=Adam(), loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# モデルのトレーニング実行
model.fit(train_images, train_labels, epochs=10, validation_data=(val_images, val_labels))

# モデルの保存
model.save('static/classifier/mnist_model_updated.h5')
print("再トレーニング完了、mnist_model_updated.h5として保存されました。")
