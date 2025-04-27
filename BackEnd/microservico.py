#!/usr/bin/env python3
import os
import sys
import grpc
from concurrent import futures
import time
import json
import threading
import asyncio
import pika

# --- Ajuste de import para encontrar o WebSocket Server ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(BASE_DIR)
WS_DIR = os.path.join(BACKEND_DIR, 'WebSocket')
if WS_DIR not in sys.path:
    sys.path.insert(0, WS_DIR)

import service_pb2
import service_pb2_grpc
from websocket_server import enviar_dados_para_todos

# Estado atual das salas (cache)
salas = {}

class AmbienteService(service_pb2_grpc.AmbienteServiceServicer):
    def ObterDadosAmbiente(self, request, context):
        # retorna apenas os campos declarados no proto: nome, temperatura e presenca
        estado = salas.get(request.sala_id, {})
        return service_pb2.AmbienteResponse(
            nome=f"Sala {request.sala_id}",
            temperatura=estado.get('temperatura', 0.0),
            presenca=estado.get('presenca', False)
        )

    def ControlarArCondicionado(self, request, context):
        # atualiza estado local
        estado = salas.setdefault(request.sala_id, {})
        estado['ar_condicionado'] = request.comando
        salas[request.sala_id] = estado

        # notifica front-end via WebSocket
        asyncio.run(enviar_dados_para_todos(estado))

        return service_pb2.ControleArResponse(status="OK")

def callback(ch, method, props, body):
    dados = json.loads(body)
    print(f"[gRPC Consumer] Recebido no Microserviço: {dados}")   # ← log completo dos dados
    salas[dados['sala_id']] = dados
    print(f"[gRPC Consumer] Enviando ao WebSocket: {dados}")      # ← log antes do broadcast
    asyncio.run(enviar_dados_para_todos(dados))


def iniciar_consumidor():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='dados_sensores')
    channel.basic_consume(
        queue='dados_sensores',
        on_message_callback=callback,
        auto_ack=True
    )
    print("[gRPC Consumer] Aguardando mensagens em RabbitMQ...")
    channel.start_consuming()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    service_pb2_grpc.add_AmbienteServiceServicer_to_server(AmbienteService(), server)
    server.add_insecure_port('[::]:5100')
    server.start()
    print("[gRPC] Servidor rodando em [::]:5100")
    # inicia consumidor RabbitMQ numa thread separada
    threading.Thread(target=iniciar_consumidor, daemon=True).start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print("\n[gRPC] Encerrando servidor...")
        server.stop(0)

if __name__ == "__main__":
    serve()
