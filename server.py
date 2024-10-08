from flask_cors import CORS
from flask import Flask, request, jsonify, render_template
from tensorflow.keras.models import load_model
import numpy as np
import cv2
import os
import datetime
import base64
import random
import logging
import time
import gc
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # CORSを有効にする

# ログ設定
logging.basicConfig(level=logging.INFO)

# mnist_model_updated.h5のロード
model_path = os.path.join('static', 'classifier', 'mnist_model_updated.h5')
if os.path.exists(model_path):
    model = load_model(model_path)
    logging.info(f"Model loaded successfully from {model_path}")
else:
    logging.error(f"Model not found at {model_path}")
    raise FileNotFoundError(f"Model not found at {model_path}")

# 保存するディレクトリ
save_dir = 'static/saved_images'
os.makedirs(save_dir, exist_ok=True)  # 保存先ディレクトリが存在しない場合作成
logging.info(f"Image save directory: {save_dir}")

# 画像の形状を正規化し、余白を取り除きつつ縦横比を保持する関数
def normalize_shape(img):
    _, img_bin = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(img_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        cnt = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(cnt)
        img = img[y:y+h, x:x+w]  # 数字の部分を切り取る

        aspect_ratio = w / h
        if aspect_ratio > 1:  # 横長の場合
            new_w = 28
            new_h = int(new_w / aspect_ratio)
        else:  # 縦長または正方形の場合
            new_h = 28
            new_w = int(new_h * aspect_ratio)
        
        # 数字の画像をリサイズ
        img_resized = cv2.resize(img, (new_w, new_h))
        
        # リサイズ後の画像を28×28のキャンバスの中央に配置する
        img_padded = np.ones((28, 28), dtype=np.uint8) * 255  # 白背景
        start_x = (28 - new_w) // 2
        start_y = (28 - new_h) // 2
        img_padded[start_y:start_y + new_h, start_x:start_x + new_w] = img_resized

        return img_padded

    # 輪郭が見つからない場合、オリジナルを返す
    return img

# 桁ごとに画像を分割する関数
def split_digits(img):
    _, img_bin = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(img_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    digit_imgs = []
    bounding_boxes = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        bounding_boxes.append((x, y, w, h))

    # 左から右へソート
    bounding_boxes = sorted(bounding_boxes, key=lambda x: x[0])

    for box in bounding_boxes:
        x, y, w, h = box
        digit_img = img[y:y + h, x:x + w]  # 各桁の画像を切り取る
        digit_img = normalize_shape(digit_img)  # 正規化して余白を消去
        digit_imgs.append(digit_img)

    return digit_imgs

# CSVファイルをランダムに取得する関数
def get_random_csv(operation):
    csv_dir = os.path.join('static', 'csv')
    csv_files = [f for f in os.listdir(csv_dir) if f.startswith(operation)]
    
    if not csv_files:
        logging.error(f"No CSV files found for operation: {operation}")
        return None

    random_csv = random.choice(csv_files)
    return os.path.join(csv_dir, random_csv)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_csv_files', methods=['GET'])
def get_csv_files():
    operation = request.args.get('operation')  # クエリパラメータから操作を取得
    csv_file = get_random_csv(operation)  # ランダムなCSVファイルを取得
    
    if csv_file and os.path.exists(csv_file):
        logging.info(f"CSV file loaded: {csv_file}")
        return jsonify({'message': 'CSV file loaded', 'path': csv_file})
    else:
        logging.error(f"CSV file not found for operation: {operation}")
        return jsonify({'message': 'CSV file not found', 'path': None}), 404

@app.route('/save_image', methods=['POST'])
def save_image():
    data = request.json
    image_data = data['image']

    try:
        # 画像データを保存
        image_data = image_data.split(",")[1]
        img = np.frombuffer(base64.b64decode(image_data), dtype=np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_GRAYSCALE)

        # 画像を正規化し、余白を削除しつつ縦横比を保持
        img = normalize_shape(img)

        # 保存用ファイル名作成
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(save_dir, 'new', f'image_{current_time}.png')
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        cv2.imwrite(save_path, img)

        logging.info(f"Image saved: {save_path}")
        return jsonify({'message': 'Image saved', 'path': save_path}), 200

    except Exception as e:
        logging.error(f"Error saving image: {e}")
        return jsonify({'error': 'Image saving failed', 'message': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        image_data = data['image']

        # 画像データを処理
        image_data = image_data.split(",")[1]
        img = np.frombuffer(base64.b64decode(image_data), dtype=np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_GRAYSCALE)

        if img is None:
            return jsonify({'error': 'Image decoding failed'}), 400

        # 画像をリサイズしてメモリ使用量を削減
        img = cv2.resize(img, (28, 28))

        # 複数桁を認識できるように画像を分割
        digit_images = split_digits(img)

        if not digit_images:
            return jsonify({'error': 'No digits found'}), 400

        # モデルでバッチ予測
        digit_images = np.array(digit_images).reshape(-1, 28, 28, 1)
        predictions = model.predict(digit_images).argmax(axis=1)

        # 複数桁の数字を結合
        result = ''.join(map(str, predictions))

        # メモリ解放
        del img, digit_images, predictions
        gc.collect()

        return jsonify({'prediction': result}), 200

    except Exception as e:
        logging.error(f"Error during prediction: {e}")
        return jsonify({'error': 'Prediction failed', 'message': str(e)}), 500

if __name__ == "__main__":
    # ローカル環境での実行用。Renderでのデプロイではgunicornが使用されるため、これは無視される
    app.run(host="0.0.0.0", port=5000, debug=True)