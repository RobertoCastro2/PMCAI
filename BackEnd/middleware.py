#!/usr/bin/env python3
import os
import sys
import asyncio
import pika
import json
import grpc

# Ajusta o path para importar WebSocket e MicroServico corretamente
dirs = []
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
micro_dir = os.path.join(backend_dir, 'MicroServico')
ws_dir = os.path.join(backend_dir, 'WebSocket')
for d in [backend_dir, micro_dir, ws_dir]:
    if d not in sys.path:
        sys.path.insert(0, d)

import service_pb2
import service_pb2_grpc
from websocket_server import enviar_dados_para_todos

# Configuração RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='dados_sensores')

# Stub gRPC
stub = None

import grpc
from grpc import FutureTimeoutError

def conectar_grpc():
    global stub
    channel = grpc.insecure_channel('localhost:5100')
    try:
        # aguarda até 5s pela conexão
        grpc.channel_ready_future(channel).result(timeout=5)
    except FutureTimeoutError:
        print("[MIDDLEWARE] gRPC não está disponível em localhost:5100")
        return False
    stub = service_pb2_grpc.AmbienteServiceStub(channel)
    print("[MIDDLEWARE] Conectado ao gRPC em localhost:5100")
    return True


# Callback para mensagens da fila
def callback(ch, method, properties, body):
    dados = json.loads(body)
    if stub is None:
        if not conectar_grpc():
            return  # pula essa mensagem, tentará novamente na próxima

    try:
        # Faz chamada gRPC para controlar o AC
        req = service_pb2.ControleArRequest(
            sala_id=dados['sala_id'],
            comando=dados.get('comando', '')
        )
        resp = stub.ControlarArCondicionado(req)
        print(f"[MIDDLEWARE] Resposta gRPC: {resp.status}")

        # Envia atualizações via WebSocket de forma síncrona
        asyncio.run(enviar_dados_para_todos({
            'sala_id': dados['sala_id'],
            'temperatura': dados.get('temperatura'),
            'presenca': dados.get('presenca'),
            'ar_condicionado': dados.get('comando')
        }))

    except Exception as e:
        print(f"[MIDDLEWARE] Erro ao processar: {e}")

print("[MIDDLEWARE] Escutando a fila 'dados_sensores'...")
channel.basic_consume(queue='dados_sensores', on_message_callback=callback, auto_ack=True)
channel.start_consuming()
