# services/processing/app/main.py
import os
from shared.config import Config
from shared.logger import setup_logger
import pika
import json
import time
from PIL import Image

logger = setup_logger('processing_service')

def process_image(filepath):
    try:
        logger.info(f"Processing image: {filepath}")
        with Image.open(filepath) as img:
            # Get original filename and extension
            filename, ext = os.path.splitext(filepath)
            
            # Resize image
            max_size = (800, 800)
            img.thumbnail(max_size, Image.LANCZOS)
            
            # Save processed image
            processed_path = f"{filename}_processed{ext}"
            img.save(processed_path)
            
            logger.info(f"Image processed and saved to: {processed_path}")
            return processed_path
            
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None

def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        filepath = message['filepath']
        logger.info(f"Processing file: {filepath}")
        
        processed_path = process_image(filepath)
        
        if processed_path:
            logger.info("Processing successful")
            message['status'] = 'processed'
            message['processed_filepath'] = processed_path
            
            # Forward to notification queue
            ch.basic_publish(
                exchange='',
                routing_key=Config.QUEUE_NOTIFICATION,
                body=json.dumps(message)
            )
        else:
            logger.error("Processing failed")
            message['status'] = 'processing_failed'
            # Send to dead letter queue
            ch.basic_publish(
                exchange='',
                routing_key=Config.QUEUE_DEAD_LETTER,
                body=json.dumps(message)
            )
            
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    config = Config()
    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASS)
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=config.RABBITMQ_HOST,
                port=config.RABBITMQ_PORT,
                credentials=credentials
            ))
            
            channel = connection.channel()
            
            # Declare all needed queues
            channel.queue_declare(queue=config.QUEUE_PROCESSING)
            channel.queue_declare(queue=config.QUEUE_NOTIFICATION)
            channel.queue_declare(queue=config.QUEUE_DEAD_LETTER)
            
            logger.info("Connected to RabbitMQ")
            
            channel.basic_consume(
                queue=config.QUEUE_PROCESSING,
                on_message_callback=callback
            )
            
            logger.info('Processing service waiting for messages...')
            channel.start_consuming()
            
        except pika.exceptions.AMQPConnectionError:
            retry_count += 1
            logger.error(f"Failed to connect to RabbitMQ. Attempt {retry_count} of {max_retries}")
            if retry_count < max_retries:
                time.sleep(5)
            else:
                raise

if __name__ == '__main__':
    main()