#!/usr/bin/env python3
import sys
import logging
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
import grpc
import service_pb2
import service_pb2_grpc

# --- Configurações do Flask + CORS + Logging ---
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
logging.basicConfig(level=logging.DEBUG)

@app.route('/api/ac', methods=['POST'])
def toggle_ac():
    try:
        # 1) Leitura e validação do JSON
        data = request.get_json(force=True)
        logging.debug(f"[HTTP] Payload recebido: {data}")

        sala_id_raw = data.get("sala_id")
        comando     = data.get("comando")

        sala_id = int(sala_id_raw)  # pode lançar ValueError
        if comando not in ("ligar", "desligar"):
            return jsonify({"msg": "comando deve ser 'ligar' ou 'desligar'"}), 400

        # 2) Cria canal e stub gRPC NO MOMENTO da requisição
        channel = grpc.insecure_channel("localhost:5100")
        grpc.channel_ready_future(channel).result(timeout=5)
        stub = service_pb2_grpc.AmbienteServiceStub(channel)

        # 3) Chama o método gRPC
        logging.debug(f"[HTTP→gRPC] sala_id={sala_id}, comando={comando}")
        req  = service_pb2.ControleArRequest(sala_id=sala_id, comando=comando)
        resp = stub.ControlarArCondicionado(req)
        logging.debug(f"[gRPC→HTTP] resposta: {resp.status}")

        # 4) Retorna o status do gRPC como JSON
        code = 200 if resp.status == "OK" else 500
        return jsonify({"msg": resp.status}), code

    except Exception as e:
        # imprime traceback no console
        traceback.print_exc()
        # retorna o texto da exceção no JSON para o front
        return jsonify({"msg": f"Erro interno no servidor: {e}"}), 500

if __name__ == "__main__":
    # desliga o reloader para não invalidar o canal gRPC
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
