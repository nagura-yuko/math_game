from tensorflow.keras.preprocessing.image import load_img, img_to_array
import os
import numpy as np
import cv2

def load_custom_data(data_dir):
    images = []
    labels = []
    for label in os.listdir(data_dir):
        label_dir = os.path.join(data_dir, label)
        
        # フォルダ名が 'new' の場合は無視
        if label == 'new':
            continue
        
        if os.path.isdir(label_dir):
            for image_file in os.listdir(label_dir):
                # `.DS_Store`ファイルを無視
                if image_file == '.DS_Store':
                    continue
                image_path = os.path.join(label_dir, image_file)
                try:
                    # 560x560 の画像を読み込み
                    img = load_img(image_path, color_mode='grayscale')
                    img_array = img_to_array(img)

                    # 28x28 にリサイズ
                    img_resized = cv2.resize(img_array, (28, 28))

                    # 形状を変更して正規化
                    img_resized = img_resized.reshape(28, 28, 1) / 255.0
                    images.append(img_resized)

                    # ラベルを追加（フォルダ名がラベルになっている）
                    labels.append(int(label))
                except Exception as e:
                    print(f"Error loading {image_path}: {e}")
    
    return np.array(images), np.array(labels)

# 使用例
# data_dir = 'static/saved_images'
# custom_images, custom_labels = load_custom_data(data_dir)
# print(f"{len(custom_images)} 枚の画像と対応するラベルを読み込みました。")
