const websocketUrl = 'ws://localhost:8765';
let socket;

function conectarWebSocket() {
    socket = new WebSocket(websocketUrl);

    socket.onopen = () => {
        console.log("[WebSocket] Conectado com sucesso.");
    };

    socket.onmessage = event => {
        console.log("[Client] mensagem recebida:", event.data);
        const dados = JSON.parse(event.data);
        const salaDiv = document.querySelector(`#sala-${dados.sala_id}`);
        if (salaDiv) {
            salaDiv.querySelector('.temp').textContent = `${dados.temperatura}°C`;
            salaDiv.querySelector('.presenca').textContent = dados.presenca ? 'Detectada' : 'Não detectada';
            salaDiv.querySelector('.ar-condicionado').textContent = dados.ar_condicionado || salaDiv.querySelector('.ar-condicionado').textContent;
        }
    };

    socket.onerror = error => console.error("[WebSocket] Erro:", error);

    socket.onclose = () => {
        console.warn("[WebSocket] Conexão fechada. Tentando reconectar em 3s...");
        setTimeout(conectarWebSocket, 3000);
    };
}

function criarSala(sala) {
    const div = document.createElement('div');
    div.classList.add('sala');
    div.id = `sala-${sala.id}`;
    div.innerHTML = `
        <h2>${sala.nome}</h2>
        <p><strong>Temperatura:</strong> <span class="temp">${sala.temperatura}°C</span></p>
        <p><strong>Presença:</strong> <span class="presenca">${sala.presenca ? 'Detectada' : 'Não detectada'}</span></p>
        <p><strong>Ar-condicionado:</strong> <span class="ar-condicionado">${sala.ar_condicionado}</span></p>
        <button class="botao ligar">Ligar AC</button>
        <button class="botao desligar">Desligar AC</button>
    `;
    div.querySelector('.ligar').onclick = () => enviarComando(sala.id, 'ligar');
    div.querySelector('.desligar').onclick = () => enviarComando(sala.id, 'desligar');
    return div;
}

function enviarComando(salaId, comando) {
    const msg = JSON.stringify({ comando, sala_id: salaId });
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(msg);
    } else {
        console.warn("WebSocket não está conectado. Comando não enviado.");
    }
}

function iniciarPainel(salas) {
    const container = document.getElementById('salas');
    salas.forEach(s => container.appendChild(criarSala(s)));
}

const salasIniciais = [
    { id:1, nome:'Sala 1', temperatura:0, presenca:false, ar_condicionado:'Desligado' },
    { id:2, nome:'Sala 2', temperatura:0, presenca:false, ar_condicionado:'Desligado' },
    { id:3, nome:'Sala 3', temperatura:0, presenca:false, ar_condicionado:'Desligado' }
];

iniciarPainel(salasIniciais);
conectarWebSocket();
