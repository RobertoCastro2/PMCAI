import socket
import json
import random
import threading
import time

GATEWAY_IP = "127.0.0.1"
GATEWAY_PORT = 5005

class Sala:
    def __init__(self, id, nome):
        self.id = id
        self.nome = nome
        self.atuador_ar_condicionado = 'Desligado'

    def simular_sensor_temperatura(self):
        # Temperatura entre 20.0 e 30.0 °C
        return round(random.uniform(20.0, 30.0), 1)

    def simular_sensor_presenca(self):
        # Presença aleatória
        return random.choice([True, False])

    def iniciar(self):
        def loop():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            while True:
                dados = {
                    'sala_id': self.id,
                    'temperatura': self.simular_sensor_temperatura(),
                    'presenca': self.simular_sensor_presenca(),
                    'ar_condicionado': self.atuador_ar_condicionado
                }
                msg = json.dumps(dados).encode()
                sock.sendto(msg, (GATEWAY_IP, GATEWAY_PORT))
                time.sleep(5)  # envia a cada 5 segundos
        threading.Thread(target=loop, daemon=True).start()

# Cria e inicia as salas
salas = [
    Sala(1, 'Sala de Aula 1'),
    Sala(2, 'Laboratório 1'),
    Sala(3, 'Auditório 1')
]

for sala in salas:
    sala.iniciar()

# Mantém o script rodando
while True:
    time.sleep(1)
