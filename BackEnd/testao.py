import grpc
import service_pb2, service_pb2_grpc

def main():
    channel = grpc.insecure_channel('localhost:5100')
    stub = service_pb2_grpc.AmbienteServiceStub(channel)

    # Teste de consulta
    resp1 = stub.ObterDadosAmbiente(
        service_pb2.DadosAmbienteRequest(sala_id=1)
    )
    print("ObterDadosAmbiente:", resp1)

    # Teste de controle
    resp2 = stub.ControlarArCondicionado(
        service_pb2.ControleArRequest(sala_id=1, comando="ligar")
    )
    print("ControlarArCondicionado:", resp2)

if __name__ == "__main__":
    main()

