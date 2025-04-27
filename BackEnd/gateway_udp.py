import socket, json, threading, pika

GATEWAY_IP = "0.0.0.0"
GATEWAY_PORT = 5005

salas_conectadas = {}

# RabbitMQ
conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
ch = conn.channel()
ch.queue_declare(queue='dados_sensores')

# UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((GATEWAY_IP, GATEWAY_PORT))

def receber_dados():
    while True:
        msg, addr = sock.recvfrom(1024)
        dados = json.loads(msg.decode())
        sala_id = dados.get('sala_id')
        if sala_id is not None:
            salas_conectadas[sala_id] = addr
            ch.basic_publish(exchange='', routing_key='dados_sensores', body=json.dumps(dados))
            print(f"[GATEWAY] Publicou Sala {sala_id}: {dados}")

def enviar_comando(sala_id, comando):
    addr = salas_conectadas.get(sala_id)
    if addr:
        msg = json.dumps({'comando': comando, 'sala_id': sala_id}).encode()
        sock.sendto(msg, addr)
        print(f"[COMANDO] Sala {sala_id} -> {comando}")
    else:
        print(f"[ERRO] Sala {sala_id} não conectada")

threading.Thread(target=receber_dados, daemon=True).start()

while True:
    entrada = input("comando (ex: 1 ligar)> ").strip().split()
    if len(entrada)==2 and entrada[0].isdigit():
        enviar_comando(int(entrada[0]), entrada[1])
    else:
        print("Formato inválido.")
