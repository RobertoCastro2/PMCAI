#!/usr/bin/env python3
import os
import sys
import pika
import json
import grpc

# Ajusta o path para importar os stubs gRPC
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

import service_pb2
import service_pb2_grpc

# Conexão RabbitMQ e fila de comandos
conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = conn.channel()
channel.queue_declare(queue='dados_sensores')

# Stub gRPC (ControlarArCondicionado)
stub = None

def conectar_grpc():
    global stub
    grpc_channel = grpc.insecure_channel('localhost:5100')
    try:
        grpc.channel_ready_future(grpc_channel).result(timeout=5)
    except Exception:
        print("[MIDDLEWARE] Não conectou ao gRPC em localhost:5100")
        return False
    stub = service_pb2_grpc.AmbienteServiceStub(grpc_channel)
    print("[MIDDLEWARE] Conectado ao gRPC em localhost:5100")
    return True

def on_message(ch, method, properties, body):
    dados = json.loads(body)
    sala_id = dados.get('sala_id')
    comando  = dados.get('comando')

    # só processa se vier um comando válido
    if not isinstance(sala_id, int) or comando not in ('ligar', 'desligar'):
        return

    if stub is None and not conectar_grpc():
        return

    try:
        req = service_pb2.ControleArRequest(
            sala_id=sala_id,
            comando=comando
        )
        resp = stub.ControlarArCondicionado(req)
        print(f"[MIDDLEWARE] gRPC respondeu: {resp.status} para sala {sala_id}")
    except Exception as e:
        print(f"[MIDDLEWARE] Erro na chamada gRPC: {e}")

print("[MIDDLEWARE] Consumindo fila 'dados_sensores' (comandos)...")
channel.basic_consume(
    queue='dados_sensores',
    on_message_callback=on_message,
    auto_ack=True
)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("[MIDDLEWARE] Encerrado pelo usuário")
    channel.stop_consuming()
    conn.close()
