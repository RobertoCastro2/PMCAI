#!/usr/bin/env python3
import socket
import json
import random
import threading
import time

GATEWAY_IP   = "127.0.0.1"
GATEWAY_PORT = 5005

class Sala:
    def __init__(self, id, nome):
        self.id = id
        self.nome = nome
        self.atuador_ar_condicionado = 'Desligado'

        # Cria um único socket UDP para enviar e receber
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # timeout curto para não bloquear eternamente
        self.sock.settimeout(0.5)

        # Thread de envio periódico de dados
        threading.Thread(target=self._enviar_loop, daemon=True).start()
        # Thread de escuta de comandos
        threading.Thread(target=self._escutar_comandos, daemon=True).start()

    def simular_sensor_temperatura(self):
        return round(random.uniform(20.0, 30.0), 1)

    def simular_sensor_presenca(self):
        return random.choice([True, False])

    def _enviar_loop(self):
        while True:
            dados = {
                'sala_id':         self.id,
                'temperatura':     self.simular_sensor_temperatura(),
                'presenca':        self.simular_sensor_presenca(),
                'ar_condicionado': self.atuador_ar_condicionado
            }
            try:
                self.sock.sendto(json.dumps(dados).encode(), (GATEWAY_IP, GATEWAY_PORT))
                print(f"[Sala {self.id}] Enviado: {dados}")
            except Exception as e:
                print(f"[Sala {self.id}] Erro enviando sensor: {e}")
            time.sleep(5)

    def _escutar_comandos(self):
        while True:
            try:
                msg, _ = self.sock.recvfrom(1024)
                cmd = json.loads(msg.decode())
                # só processa comandos para esta sala
                if cmd.get('sala_id') == self.id:
                    ac = cmd.get('comando', '').lower()
                    if ac == 'ligar':
                        self.atuador_ar_condicionado = 'Ligado'
                    elif ac == 'desligar':
                        self.atuador_ar_condicionado = 'Desligado'
                    print(f"[Sala {self.id}] Comando recebido: {ac} → {self.atuador_ar_condicionado}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[Sala {self.id}] Erro recepção comando: {e}")

# cria e inicia as salas
salas = [
    Sala(1, 'Sala de Aula 1'),
    Sala(2, 'Laboratório 1'),
    Sala(3, 'Auditório 1')
]

# mantém o script vivo
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Simulador de salas encerrado")
