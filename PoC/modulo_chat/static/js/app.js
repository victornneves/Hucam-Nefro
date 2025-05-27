// =================== VARIÁVEIS E ELEMENTOS ===================
const patientId = document.getElementById('patient-id').textContent;

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
  document.getElementById('patient-age').textContent = '45 anos';
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
    document.documentElement.style.setProperty('--progress', `${progress}%`);
  });

  // Controle play/pause
  playButton.addEventListener('click', () => {
    if (audioPlayer.paused) {
      audioPlayer.play();
      playButton.innerHTML = '<img src="/static/images/pausa.png" alt="Pause" style="height: 20px;">';
    } else {
      audioPlayer.pause();
      playButton.innerHTML = '<img src="/static/images/botao-play.png" alt="Play" style="height: 20px;">';
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
  playButton.innerHTML = '<img src="/static/images/botao-play.png" alt="Play" style="height: 20px;">';
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
