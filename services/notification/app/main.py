# services/notification/app/main.py
import pika
import json
from shared.config import Config
from shared.logger import setup_logger
import time

logger = setup_logger('notification_service')
config = Config()

def callback(ch, method, properties, body):
    message = json.loads(body)
    # In real app, you would send email/notification here
    logger.info(f"Processing completed for file: {message['filename']}")
    logger.info(f"Processed file path: {message.get('processed_filepath', 'N/A')}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

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
def main():
    connection = get_rabbitmq_connection()
    
    channel = connection.channel()
    channel.queue_declare(queue=config.QUEUE_NOTIFICATION)
    
    channel.basic_consume(
        queue=config.QUEUE_NOTIFICATION,
        on_message_callback=callback
    )
    
    logger.info('Notification service waiting for messages...')
    channel.start_consuming()

if __name__ == '__main__':
    main()