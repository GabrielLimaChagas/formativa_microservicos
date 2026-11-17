import json
import logging
import threading
from typing import Dict, Any, List
from domain.repositories import EventConsumer
from application.events import AuditService

logger = logging.getLogger(__name__)

class AzureServiceBusEventConsumer(EventConsumer):
    def __init__(self, connection_string: str, queue_name: str, audit_service: AuditService, app_context_provider=None):
        self.connection_string = connection_string
        self.queue_name = queue_name
        self.audit_service = audit_service
        self.app_context_provider = app_context_provider
        self._thread = None
        self._running = False

    def process_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self.app_context_provider:
            with self.app_context_provider():
                self.audit_service.log_event(event_type, payload)
        else:
            self.audit_service.log_event(event_type, payload)

    def start_listening(self) -> None:
        if not self.connection_string:
            logger.info("[AzureServiceBusEventConsumer] AZURE_SERVICEBUS_CONNECTION_STRING vazia. Modo background listener ativo para fallback local.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info(f"[AzureServiceBusEventConsumer] Thread de escuta iniciada na fila '{self.queue_name}'.")

    def _listen_loop(self):
        try:
            from azure.servicebus import ServiceBusClient
            with ServiceBusClient.from_connection_string(self.connection_string) as client:
                with client.get_queue_receiver(self.queue_name) as receiver:
                    for msg in receiver:
                        if not self._running:
                            break
                        try:
                            body_str = str(msg)
                            data = json.loads(body_str)
                            event_type = data.get("eventType", "UnknownEvent")
                            payload = data.get("payload", {})
                            self.process_event(event_type, payload)
                            receiver.complete_message(msg)
                        except Exception as ex:
                            logger.error(f"[AzureServiceBusEventConsumer] Falha ao processar mensagem: {ex}")
        except Exception as e:
            logger.error(f"[AzureServiceBusEventConsumer] Erro de conexão com Azure Service Bus: {e}")

    def drain_queue_once(self, max_messages: int = 10) -> int:
        """
        Processamento sob demanda da fila do Azure Service Bus.
        Retorna a quantidade de mensagens processadas.
        """
        if not self.connection_string:
            return 0

        processed = 0
        try:
            from azure.servicebus import ServiceBusClient
            with ServiceBusClient.from_connection_string(self.connection_string) as client:
                with client.get_queue_receiver(self.queue_name, max_message_count=max_messages) as receiver:
                    messages = receiver.receive_messages(max_message_count=max_messages, max_wait_time=3.0)
                    for msg in messages:
                        try:
                            data = json.loads(str(msg))
                            event_type = data.get("eventType", "UnknownEvent")
                            payload = data.get("payload", {})
                            self.process_event(event_type, payload)
                            receiver.complete_message(msg)
                            processed += 1
                        except Exception as ex:
                            logger.error(f"Erro ao processar mensagem sob demanda: {ex}")
        except Exception as e:
            logger.error(f"Erro ao drenar fila do Service Bus: {e}")

        return processed
