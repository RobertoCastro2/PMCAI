import grpc
import service_pb2
import service_pb2_grpc

def main():
    channel = grpc.insecure_channel('localhost:5100')
    stub = service_pb2_grpc.AmbienteServiceStub(channel)

    # 1) Testa ObterDadosAmbiente
    req1 = service_pb2.AmbienteRequest(sala_id=1)
    resp1 = stub.ObterDadosAmbiente(req1)
    print("ObterDadosAmbiente:", resp1)

    # 2) Testa ControlarArCondicionado
    req2 = service_pb2.ControleArRequest(sala_id=1, comando="ligar")
    resp2 = stub.ControlarArCondicionado(req2)
    print("ControlarArCondicionado:", resp2)

if __name__ == "__main__":
    main()
