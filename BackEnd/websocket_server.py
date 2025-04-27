#!/usr/bin/env python3
import asyncio
import websockets
import json
import threading
import pika

# Conjunto de clientes WebSocket conectados
clientes = set()
# Loop principal do asyncio, atribuído no main()
loop = None

async def handler(websocket, path):
    clientes.add(websocket)
    print("[WebSocket] Cliente conectado")
    try:
        # Aguarda o cliente enviar mensagens ou desconectar
        async for message in websocket:
            print(f"[WebSocket] Mensagem recebida do cliente: {message}")
            # Aqui você poderia tratar comandos vindos do front-end,
            # por exemplo, chamando um gRPC ou publicando numa fila.
            # Mas como foco é receber dados de sensores, deixamos para o RabbitMQ.
        await websocket.wait_closed()
    finally:
        clientes.remove(websocket)
        print("[WebSocket] Cliente desconectado")

def rabbit_consumer():
    """Thread que consome a fila 'dados_sensores' e faz broadcast."""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='dados_sensores')

    def callback(ch, method, properties, body):
        dados = json.loads(body)
        mensagem = json.dumps(dados)
        print(f"[RabbitConsumer] Broadcast para {len(clientes)} clientes: {mensagem}")
        if clientes:
            # Agenda o envio das mensagens no loop asyncio principal
            asyncio.run_coroutine_threadsafe(
                asyncio.gather(*(c.send(mensagem) for c in list(clientes))),
                loop
            )

    channel.basic_consume(
        queue='dados_sensores',
        on_message_callback=callback,
        auto_ack=True
    )
    print("[RabbitConsumer] Iniciando consumo da fila 'dados_sensores'...")
    channel.start_consuming()

async def main():
    global loop
    print("[WebSocket] Servidor rodando em ws://localhost:8765")
    async with websockets.serve(handler, "localhost", 8765):
        loop = asyncio.get_running_loop()
        # Inicia o consumidor RabbitMQ em thread separada
        threading.Thread(target=rabbit_consumer, daemon=True).start()
        # Mantém o servidor rodando
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
