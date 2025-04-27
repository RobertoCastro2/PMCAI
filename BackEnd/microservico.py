#!/usr/bin/env python3
import os
import sys
import json
import threading
import queue
import pika
import grpc
from concurrent import futures

import service_pb2
import service_pb2_grpc

# -----------------------------------------------------------------------------
# Setup do RabbitMQ: conexão, canal e fila
rabbit_conn    = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
rabbit_channel = rabbit_conn.channel()
rabbit_channel.queue_declare(queue='dados_sensores')

# Fila thread-safe para payloads a publicar
publish_queue = queue.Queue()

def rabbit_publisher():
    """Thread dedicada a publicar no RabbitMQ."""
    while True:
        payload = publish_queue.get()
        if payload is None:
            break  # para limpeza futura, se desejar
        try:
            rabbit_channel.basic_publish(
                exchange='',
                routing_key='dados_sensores',
                body=json.dumps(payload)
            )
            print(f"[Publisher] Enviado payload: {payload}")
        except Exception as e:
            print(f"[Publisher] Erro ao publicar: {e}")
        finally:
            publish_queue.task_done()

# Inicia a thread de publicação
threading.Thread(target=rabbit_publisher, daemon=True).start()

# -----------------------------------------------------------------------------
# Cache de estado das salas em memória
salas = {}

class AmbienteService(service_pb2_grpc.AmbienteServiceServicer):
    def ObterDadosAmbiente(self, request, context):
        estado = salas.get(request.sala_id, {})
        return service_pb2.AmbienteResponse(
            nome=f"Sala {request.sala_id}",
            temperatura=estado.get('temperatura', 0.0),
            presenca=estado.get('presenca', False),
            ar_condicionado=estado.get('ar_condicionado', 'desligar')
        )

    def ControlarArCondicionado(self, request, context):
        # Atualiza estado local
        estado = salas.setdefault(request.sala_id, {})
        estado['ar_condicionado'] = request.comando
        salas[request.sala_id] = estado

        # Enfileira payload para broadcast via RabbitMQ
        payload = {
            'sala_id':     request.sala_id,
            'comando':     request.comando,
            'temperatura': estado.get('temperatura'),
            'presenca':    estado.get('presenca')
        }
        publish_queue.put(payload)

        return service_pb2.ControleArResponse(status="OK")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    service_pb2_grpc.add_AmbienteServiceServicer_to_server(AmbienteService(), server)
    server.add_insecure_port('[::]:5100')
    server.start()
    print("[gRPC] Servidor rodando em [::]:5100")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
