# shared/config.py
from dataclasses import dataclass, field
from typing import Set
import os

@dataclass
class Config:
    UPLOAD_DIR: str = os.getenv('UPLOAD_DIR', 'uploads')
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS: Set[str] = field(
        default_factory=lambda: {'png', 'jpg', 'jpeg', 'gif'}
    )
    
    # RabbitMQ Config
    RABBITMQ_HOST: str = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT: int = int(os.getenv('RABBITMQ_PORT', 5672))
    RABBITMQ_USER: str = os.getenv('RABBITMQ_USER', 'guest')
    RABBITMQ_PASS: str = os.getenv('RABBITMQ_PASS', 'guest')
    
    # Queue Names
    QUEUE_VALIDATION: str = 'validation'
    QUEUE_PROCESSING: str = 'processing'
    QUEUE_NOTIFICATION: str = 'notification'
    QUEUE_DEAD_LETTER: str = 'dead-letter'