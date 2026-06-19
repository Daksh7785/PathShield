import json
import logging
from typing import Callable, Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EventBroker")

class EventBroker:
    """Simulates NATS / Apache Kafka distributed event streaming for RouteGuard microservices."""
    def __init__(self):
        # In-memory subscription list: topic -> List[callbacks]
        self.subscribers: Dict[str, List[Callable]] = {}

    def publish(self, topic: str, payload: Dict):
        """Publishes a JSON payload to a NATS/Kafka topic."""
        message_str = json.dumps(payload)
        logger.info(f"[PUBLISH] Topic: '{topic}' | Payload: {message_str}")
        
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                try:
                    callback(payload)
                except Exception as e:
                    logger.error(f"Error executing callback on topic '{topic}': {e}")

    def subscribe(self, topic: str, callback: Callable):
        """Subscribes a listener callback to a NATS/Kafka topic."""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
        logger.info(f"[SUBSCRIBE] Registered subscriber for topic: '{topic}'")
