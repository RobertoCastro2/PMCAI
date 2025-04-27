import pika
import json

def callback(ch, method, properties, body):
    dados = json.loads(body)
    print(f"[CONSUMIDOR] Dados recebidos da fila: {json.dumps(dados, indent=2)}")

# Conectar ao RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()

# Declarar a fila (garantir existência)
channel.queue_declare(queue='dados_sensores')

# Consumir da fila
channel.basic_consume(queue='dados_sensores', on_message_callback=callback, auto_ack=True)

print("[CONSUMIDOR] Aguardando mensagens...")
channel.start_consuming()
