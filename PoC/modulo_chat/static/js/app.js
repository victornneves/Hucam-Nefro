// =================== VARIÁVEIS E ELEMENTOS ===================
const patientId = 18;

// Elementos do Chat
const chatContainer = document.getElementById('chat-container');
const questionInput = document.getElementById('question-input');
const sendButton = document.getElementById('send-button');
const loadingIndicator = document.getElementById('loading-indicator');

// Elementos do Player de Áudio
const audioPlayer = document.getElementById('audio-player');
const playButton = document.getElementById('play-button');
const progressBar = document.getElementById('progress-bar');
const timeDisplay = document.getElementById('time-display');
const durationDisplay = document.getElementById('duration-display');
const muteButton = document.getElementById('mute-button');
const volumeControl = document.getElementById('volume-control');
const muteIcon = document.getElementById('mute-icon');
const dbMeterLevel = document.querySelector('.db-meter-level');

// Audio context for analyzing audio levels
let audioContext;
let analyser;
let dataArray;
let source;

// MOCK
// const dados = {
//   exames: [
//     {
//       data: '2023-10-01',
//       tipo: 'Ultrassonografia',
      
//     }
//   ]
// }

// =================== FUNÇÕES UTILITÁRIAS ===================

// Formata tempo em mm:ss
function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// =================== FUNÇÕES DO CHAT ===================

// Simula carregamento de dados do paciente
function loadPatientData() {
  document.getElementById('patient-name').textContent = 'João da Silva';
  document.getElementById('patient-gender').textContent = 'Masculino';
  document.getElementById('patient-age').textContent = '45 anos';
  // document.getElementById('patient-id').textContent = '018';
  
  // Contatos
  document.getElementById('patient-phone').textContent = '(27) 99999-9999';
  document.getElementById('patient-email').textContent = 'joao.silva@email.com';
  // document.getElementById('patient-address').textContent = 'Rua das Flores, 123 - Centro - Vitória/ES';
  
  // Contato de emergência
  document.getElementById('emergency-name').textContent = 'Maria da Silva';
  // document.getElementById('emergency-relation').textContent = 'Esposa';
  document.getElementById('emergency-phone').textContent = '(27) 98888-8888';
}

// Adiciona mensagem ao chat
function addMessage(text, isQuestion) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${isQuestion ? 'question' : 'answer'}`;
  messageDiv.textContent = text;
  chatContainer.appendChild(messageDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Envia pergunta para a API
async function sendQuestion() {
  const question = questionInput.value.trim();
  if (!question) return;

  addMessage(question, true);
  questionInput.value = '';
  loadingIndicator.style.display = 'block';

  try {
    const response = await fetch('http://localhost:5003/getMedicalResponse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient: patientId, question })
    });

    if (!response.ok) throw new Error(`Erro HTTP: ${response.statusText}`);
    const data = await response.json();

    if (data.error) {
      addMessage(`Erro: ${data.error}`, false);
    } else {
      addMessage(data.response, false);
    }
  } catch (error) {
    addMessage(`Erro: ${error.message}`, false);
  } finally {
    loadingIndicator.style.display = 'none';
  }
}

// =================== FUNÇÕES DO PLAYER DE ÁUDIO ===================

function initializeAudioPlayer() {
  // Carrega duração ao abrir
  audioPlayer.addEventListener('loadedmetadata', () => {
    durationDisplay.textContent = formatTime(audioPlayer.duration);
    document.documentElement.style.setProperty('--progress', '0%');
  });

  // Atualiza barra de progresso
  audioPlayer.addEventListener('timeupdate', () => {
    const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
    progressBar.value = progress;
    timeDisplay.textContent = formatTime(audioPlayer.currentTime);

    // Atualiza a cor da barra de progresso
    progressBar.style.background = `linear-gradient(to right, #3498db ${progress}%, #ddd ${progress}%)`;
  });

  // Controle play/pause
  playButton.addEventListener('click', () => {
    if (!audioContext) {
      initAudioContext();
    }

    if (audioContext.state === 'suspended') {
      audioContext.resume();
    }

    if (audioPlayer.paused) {
      audioPlayer.play();
      playButton.innerHTML = `<img src="/static/images/pausa.png" alt="Pause">`; // Altera para imagem de pausa
      updateDBMeter();
    } else {
      audioPlayer.pause();
      playButton.innerHTML = `<img src="/static/images/botao-play.png" alt="Play">`; // Altera para imagem de play
    }
  });

  // Controle manual do progresso
  progressBar.addEventListener('input', () => {
    const seekTime = (progressBar.value / 100) * audioPlayer.duration;
    audioPlayer.currentTime = seekTime;
  });

  // Controle de volume
  volumeControl.addEventListener('input', () => {
    audioPlayer.volume = volumeControl.value;
    const volumePercent = volumeControl.value * 100;
    document.documentElement.style.setProperty('--volume', `${volumePercent}%`);
    muteIcon.src = audioPlayer.volume === 0 ? "/static/images/mudo.png" : "/static/images/volume.png";

    // Atualiza a cor da barra de volume
    volumeControl.style.background = `linear-gradient(to right, #3498db ${volumePercent}%, #ddd ${volumePercent}%)`;
  });

  // Botão de mudo
  muteButton.addEventListener('click', () => {
    if (audioPlayer.volume > 0) {
      audioPlayer.volume = 0;
      volumeControl.value = 0;
      muteIcon.src = "/static/images/mudo.png";
    } else {
      audioPlayer.volume = 1;
      volumeControl.value = 1;
      muteIcon.src = "/static/images/volume.png";
    }
  });

  // Configurações iniciais
  audioPlayer.load();
  audioPlayer.volume = 1;
  volumeControl.value = 1;
  playButton.innerHTML = `<img src="/static/images/botao-play.png" alt="Play">`;
  document.documentElement.style.setProperty('--volume', '100%');
}

// =================== ABAS DE EXAMES =====================
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    // Remove estado ativo de todas as abas
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

    // Adiciona estado ativo à aba clicada e ao painel correspondente
    tab.classList.add('active');
    const panelId = tab.dataset.tab;
    document.getElementById(panelId).classList.add('active');
  });
});

// Abas de informações do paciente
// Alterna o conteúdo das abas de informações do paciente

document.querySelectorAll('.info-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    // Remove estado ativo de todas as abas
    document.querySelectorAll('.info-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.info-panel').forEach(p => p.classList.remove('active'));

    // Adiciona estado ativo à aba clicada e ao painel correspondente
    tab.classList.add('active');
    const panelId = tab.dataset.infoTab;
    document.getElementById(panelId).classList.add('active');
  });
});

// =================== EVENTOS E INICIALIZAÇÃO ===================

window.addEventListener('load', () => {
  loadPatientData();
  initializeAudioPlayer();
  addMessage("Bem-vindo ao sistema de assistência nefrológica. Como posso ajudar?", false);
});

sendButton.addEventListener('click', sendQuestion);
questionInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendQuestion();
});

// Initialize audio context and analyzer
function initAudioContext() {
  try {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.8;
    dataArray = new Uint8Array(analyser.frequencyBinCount);
    
    source = audioContext.createMediaElementSource(audioPlayer);
    source.connect(analyser);
    analyser.connect(audioContext.destination);
    
    console.log('Audio context initialized successfully');
  } catch (error) {
    console.error('Error initializing audio context:', error);
  }
}

// Update decibel meter
function updateDBMeter() {
  if (!analyser) return;
  
  function update() {
    analyser.getByteFrequencyData(dataArray);
    const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
    
    // Convert to decibels (0-255 to -60-0 dB)
    const db = 20 * Math.log10(average / 255);
    const normalizedDb = Math.max(-60, Math.min(0, db));
    const percentage = ((normalizedDb + 60) / 60) * 100;
    
    dbMeterLevel.style.width = `${percentage}%`;
    
    if (!audioPlayer.paused) {
      requestAnimationFrame(update);
    }
  }
  
  update();
}

// Remove the one-time click event listener since we'll initialize on play
document.removeEventListener('click', () => {
  if (!audioContext) {
    initAudioContext();
  }
}, { once: true });

// Variável global para armazenar a instância do gráfico
let examChart = null;

// Função para carregar os detalhes do exame
async function loadExamDetails(examCode) {
    try {
        const response = await fetch(`/static/data/exam_details.json`);
        const data = await response.json();
        const examData = data[examCode];
        
        if (!examData) {
            console.error('Exame não encontrado:', examCode);
            return;
        }

        // Atualizar o título do modal
        document.querySelector('.modal-header h2').textContent = examData.name;

        // Atualizar a descrição
        document.querySelector('.exam-description p').textContent = examData.description;

        // Atualizar os valores
        const valuesContainer = document.querySelector('.exam-values');
        valuesContainer.innerHTML = `
            <div class="value-item">
                <span class="label">Valor Atual:</span>
                <span class="value">${examData.history[0].value} ${examData.unit}</span>
            </div>
            <div class="value-item">
                <span class="label">Valor de Referência:</span>
                <span class="value">${examData.reference_range} ${examData.unit}</span>
            </div>
        `;

        // Destruir o gráfico anterior se existir
        if (examChart) {
            examChart.destroy();
        }

        // Criar o novo gráfico
        const ctx = document.getElementById('examChart').getContext('2d');
        examChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: examData.history.map(v => v.date),
                datasets: [{
                    label: examData.name,
                    data: examData.history.map(v => v.value),
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

        // Atualizar as referências
        const literatureList = document.querySelector('.literature-list');
        literatureList.innerHTML = examData.literature.map(ref => `
            <div class="literature-item">
                <h4>${ref.title}</h4>
                <div class="authors">${ref.authors}</div>
                <div class="journal">${ref.journal}</div>
                <a href="${ref.url}" target="_blank">Ver artigo</a>
            </div>
        `).join('');

        // Mostrar o modal
        document.getElementById('examModal').style.display = 'block';
    } catch (error) {
        console.error('Erro ao carregar detalhes do exame:', error);
    }
}

// Adicionar event listeners para os elementos com valores anormais
document.querySelectorAll('.abnormal-value').forEach(element => {
    element.addEventListener('click', (e) => {
        const examCode = e.target.getAttribute('data-exam-code');
        if (examCode) {
            loadExamDetails(examCode);
        }
    });
});

// Fechar o modal
document.querySelector('.close-button').addEventListener('click', () => {
    document.getElementById('examModal').style.display = 'none';
    // Destruir o gráfico ao fechar o modal
    if (examChart) {
        examChart.destroy();
        examChart = null;
    }
});

// Fechar o modal ao clicar fora dele
window.addEventListener('click', (e) => {
    const modal = document.getElementById('examModal');
    if (e.target === modal) {
        modal.style.display = 'none';
        // Destruir o gráfico ao fechar o modal
        if (examChart) {
            examChart.destroy();
            examChart = null;
        }
    }
});

// Prontuário Modal
const prontuarioModal = document.getElementById('prontuarioModal');
const downloadProntuarioBtn = document.getElementById('download-prontuario');
const prontuarioText = document.getElementById('prontuario-text');
const prontuarioCloseBtn = prontuarioModal.querySelector('.close-button');

// Load prontuario content
fetch('/static/data/prontuario.txt')
  .then(response => response.text())
  .then(text => {
    prontuarioText.textContent = text;
  })
  .catch(error => {
    console.error('Error loading prontuario:', error);
    prontuarioText.textContent = 'Erro ao carregar o prontuário.';
  });

// Open modal
downloadProntuarioBtn.addEventListener('click', () => {
  prontuarioModal.style.display = 'block';
});

// Close modal
prontuarioCloseBtn.addEventListener('click', () => {
  prontuarioModal.style.display = 'none';
});

// Close modal when clicking outside
window.addEventListener('click', (event) => {
  if (event.target === prontuarioModal) {
    prontuarioModal.style.display = 'none';
  }
});
