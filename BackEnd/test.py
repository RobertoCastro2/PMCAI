import grpc
import service_pb2
import service_pb2_grpc

def run():
    # Conectando ao servidor gRPC
    channel = grpc.insecure_channel('localhost:5100')
    stub = service_pb2_grpc.AmbienteServiceStub(channel)

    # Testando a solicitação de dados do ambiente
    response = stub.ObterDadosAmbiente(service_pb2.AmbienteRequest(sala_id=1))
    print(f"Dados da Sala: {response.nome} - Temperatura: {response.temperatura}°C - Presença: {'Detectada' if response.presenca else 'Não detectada'} - Ar-condicionado: {response.ar_condicionado}")

    # Testando o controle do ar-condicionado
    controle_response = stub.ControlarArCondicionado(service_pb2.ControleArRequest(sala_id=1, comando="ligar"))
    print(f"Status do Ar-condicionado: {controle_response.status}")

if __name__ == '__main__':
    run()
