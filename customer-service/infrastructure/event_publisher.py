import json
import logging
from typing import Dict, Any
from application.events import EventPublisher

logger = logging.getLogger(__name__)

# Fila in-memory compartilhada para fallback em testes locais
_IN_MEMORY_EVENT_BUS = []

def get_in_memory_event_bus():
    return _IN_MEMORY_EVENT_BUS

def clear_in_memory_event_bus():
    _IN_MEMORY_EVENT_BUS.clear()

class InMemoryEventPublisher(EventPublisher):
    def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        event = {
            "eventType": event_type,
            "payload": payload
        }
        _IN_MEMORY_EVENT_BUS.append(event)
        logger.info(f"[InMemoryEventPublisher] Evento publicado: {event_type}")

class AzureServiceBusEventPublisher(EventPublisher):
    def __init__(self, connection_string: str, queue_name: str):
        self.connection_string = connection_string
        self.queue_name = queue_name

    def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        if not self.connection_string:
            InMemoryEventPublisher().publish(event_type, payload)
            return

        try:
            from azure.servicebus import ServiceBusClient, ServiceBusMessage
            with ServiceBusClient.from_connection_string(self.connection_string) as client:
                with client.get_queue_sender(self.queue_name) as sender:
                    message_data = json.dumps({"eventType": event_type, "payload": payload})
                    message = ServiceBusMessage(message_data)
                    sender.send_messages(message)
                    logger.info(f"[AzureServiceBusEventPublisher] Evento '{event_type}' enviado para fila '{self.queue_name}'.")
        except Exception as e:
            logger.error(f"[AzureServiceBusEventPublisher] Erro ao enviar mensagem para Service Bus: {e}")
            # Faz fallback em memória para não travar a aplicação em caso de indisponibilidade transitória
            InMemoryEventPublisher().publish(event_type, payload)
