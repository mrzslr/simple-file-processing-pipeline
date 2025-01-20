# services/validation/app/main.py
import os
from shared.config import Config
from shared.logger import setup_logger
import pika
import json
import time

logger = setup_logger('validation_service')

def validate_file(filepath):
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return False
            
        # Check file size (max 10MB)
        file_size = os.path.getsize(filepath)
        if file_size > 10 * 1024 * 1024:
            logger.error(f"File too large: {file_size} bytes")
            return False
            
        # Check file extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        ext = filepath.rsplit('.', 1)[1].lower()
        if ext not in allowed_extensions:
            logger.error(f"Invalid extension: {ext}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False

def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        filepath = message['filepath']
        logger.info(f"Validating file: {filepath}")
        
        if validate_file(filepath):
            logger.info("File validated successfully")
            message['status'] = 'validated'
            # Forward to processing queue
            ch.basic_publish(
                exchange='',
                routing_key=Config.QUEUE_PROCESSING,
                body=json.dumps(message)
            )
        else:
            logger.error("File validation failed")
            message['status'] = 'validation_failed'
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
            channel.queue_declare(queue=config.QUEUE_VALIDATION)
            channel.queue_declare(queue=config.QUEUE_PROCESSING)
            channel.queue_declare(queue=config.QUEUE_DEAD_LETTER)
            
            logger.info("Connected to RabbitMQ")
            
            channel.basic_consume(
                queue=config.QUEUE_VALIDATION,
                on_message_callback=callback
            )
            
            logger.info('Validation service waiting for messages...')
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