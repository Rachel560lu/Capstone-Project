from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': '没有上传图片'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400

        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        original_filename = f"{file_id}_original.png"
        processed_filename = f"{file_id}_processed.png"

        original_path = os.path.join(UPLOAD_FOLDER, original_filename)
        processed_path = os.path.join(OUTPUT_FOLDER, processed_filename)

        # 保存原始图片
        image = Image.open(file.stream)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(original_path, 'PNG')

        # 演示：直接复制图片作为"处理后的图片"
        image.save(processed_path, 'PNG')

        return jsonify({
            'success': True,
            'original_url': f'/uploads/{original_filename}',
            'processed_url': f'/output/{processed_filename}',
            'message': '演示模式：图片已接收（实际AI处理需要完整环境）'
        })

    except Exception as e:
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route('/output/<filename>')
def serve_output(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename))

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'mode': 'demo'})

if __name__ == '__main__':
    print("启动房产视觉增强系统后端服务（演示模式）...")
    print("访问 http://localhost:5000/health 检查服务状态")
    app.run(host='0.0.0.0', port=5000, debug=True)