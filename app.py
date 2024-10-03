from flask import Flask, request, jsonify
import base64
import os

app = Flask(__name__)

# 保存ディレクトリを作成
SAVE_DIR = 'saved_images'
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 画像を保存するエンドポイント
@app.route('/save_image', methods=['POST'])
def save_image():
    data = request.json['image']
    
    # Base64エンコードされたデータURLから画像部分を抽出
    image_data = base64.b64decode(data.split(',')[1])
    
    # ファイル名を生成して保存
    file_path = os.path.join(SAVE_DIR, 'handwritten_digit.png')
    with open(file_path, 'wb') as f:
        f.write(image_data)
    
    return jsonify({"message": "画像が保存されました", "file_path": file_path})

if __name__ == '__main__':
    app.run(debug=True)
