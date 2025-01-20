# services/upload/app/main.py
from flask import Flask, request, jsonify
import os
from shared.config import Config
from shared.logger import setup_logger
import pika
import json
import time

logger = setup_logger('upload_service')

app = Flask(__name__)
config = Config()
os.makedirs(config.UPLOAD_DIR, exist_ok=True)

def get_rabbitmq_connection():
    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASS)
            parameters = pika.ConnectionParameters(
                host=config.RABBITMQ_HOST,
                port=config.RABBITMQ_PORT,
                credentials=credentials
            )
            return pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError:
            retry_count += 1
            logger.error(f"Failed to connect to RabbitMQ. Attempt {retry_count} of {max_retries}")
            if retry_count < max_retries:
                time.sleep(5)  # Wait 5 seconds before retrying
            else:
                raise

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filepath = os.path.join(config.UPLOAD_DIR, file.filename)
        file.save(filepath)
        
        # Send to RabbitMQ
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        channel.queue_declare(queue=config.QUEUE_VALIDATION)
        
        message = {
            'filepath': filepath,
            'filename': file.filename
        }
        
        channel.basic_publish(
            exchange='',
            routing_key=config.QUEUE_VALIDATION,
            body=json.dumps(message)
        )
        
        connection.close()
        
        return jsonify({'message': 'File uploaded successfully', 'filepath': filepath})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)