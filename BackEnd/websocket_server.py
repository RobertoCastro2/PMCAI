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

async def handler(websocket, path=None):
    """
    Adiciona o cliente, espera desconexão e remove.
    """
    clientes.add(websocket)
    print("[WebSocket] Cliente conectado")
    try:
        async for _ in websocket:
            pass
        await websocket.wait_closed()
    finally:
        clientes.remove(websocket)
        print("[WebSocket] Cliente desconectado")

def rabbit_consumer():
    """
    Thread que consome 'dados_sensores' e broadcasta para todos os clientes.
    """
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    ch   = conn.channel()
    ch.queue_declare(queue='dados_sensores')

    def on_message(ch, method, props, body):
        dados = json.loads(body)
        msg   = json.dumps(dados)
        print(f"[RabbitConsumer] Broadcast para {len(clientes)} clientes: {msg}")
        # para cada cliente, agenda o send() no loop principal
        for c in list(clientes):
            asyncio.run_coroutine_threadsafe(
                c.send(msg),
                loop
            )

    ch.basic_consume(
        queue='dados_sensores',
        on_message_callback=on_message,
        auto_ack=True
    )
    print("[RabbitConsumer] Iniciando consumo da fila 'dados_sensores'...")
    ch.start_consuming()

async def main():
    global loop
    print("[WebSocket] Servidor rodando em ws://localhost:8765")
    async with websockets.serve(handler, "localhost", 8765):
        loop = asyncio.get_running_loop()
        threading.Thread(target=rabbit_consumer, daemon=True).start()
        # mantém o servidor vivo
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
