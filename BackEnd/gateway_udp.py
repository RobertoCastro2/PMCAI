#!/usr/bin/env python3
import socket
import json
import threading
import time
import pika

# UDP gateway configuration
GATEWAY_IP   = "0.0.0.0"
GATEWAY_PORT = 5005

# Map sala_id → (ip, port) of last sensor packet
salas_conectadas = {}

# Create UDP socket for both sending and receiving
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((GATEWAY_IP, GATEWAY_PORT))

# RabbitMQ connection & channels (one for publish, one for consume)
conn_pub  = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
pub_ch    = conn_pub.channel()
pub_ch.queue_declare(queue='dados_sensores')

conn_cons = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
cons_ch   = conn_cons.channel()
cons_ch.queue_declare(queue='dados_sensores')


def receber_dados():
    """Recebe datagramas UDP dos simuladores e publica no RabbitMQ."""
    print(f"[GATEWAY] UDP listening on {GATEWAY_IP}:{GATEWAY_PORT}")
    while True:
        msg, addr = sock.recvfrom(1024)
        try:
            dados = json.loads(msg.decode())
        except Exception as e:
            print(f"[GATEWAY] JSON decode error: {e}")
            continue

        sala_id = dados.get('sala_id')
        if sala_id is None:
            continue

        # mantém o endereço para enviar comandos depois
        salas_conectadas[sala_id] = addr

        # publica todo payload (sensores e comandos) em RabbitMQ
        pub_ch.basic_publish(
            exchange='',
            routing_key='dados_sensores',
            body=json.dumps(dados)
        )
        print(f"[GATEWAY] Publicou no broker: Sala {sala_id} → {dados}")


def consumir_comandos():
    """Consome fila RabbitMQ e envia comandos UDP aos simuladores."""
    def callback(ch, method, props, body):
        try:
            dados = json.loads(body)
        except Exception as e:
            print(f"[GATEWAY] JSON decode error in consumer: {e}")
            return

        # só trata payloads de comando
        if 'comando' not in dados or 'sala_id' not in dados:
            return

        sala_id = dados['sala_id']
        addr = salas_conectadas.get(sala_id)
        if not addr:
            print(f"[GATEWAY] Endereço desconhecido para sala {sala_id}, comando ignorado")
            return

        # envia o mesmo JSON via UDP para o simulador
        try:
            sock.sendto(json.dumps(dados).encode(), addr)
            print(f"[GATEWAY] Enviado comando UDP a Sala {sala_id}: {dados}")
        except Exception as e:
            print(f"[GATEWAY] Erro enviando comando UDP: {e}")

    cons_ch.basic_consume(
        queue='dados_sensores',
        on_message_callback=callback,
        auto_ack=True
    )
    print("[GATEWAY] Consumidor de comandos ativo")
    cons_ch.start_consuming()


if __name__ == "__main__":
    # inicia as threads de recebimento e consumo
    threading.Thread(target=receber_dados, daemon=True).start()
    threading.Thread(target=consumir_comandos, daemon=True).start()

    # mantém o processo vivo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[GATEWAY] Encerrando")
        conn_pub.close()
        conn_cons.close()
        sock.close()
