// ----- Globale Variablen -----
let mediaRecorder;
let audioChunks = [];
let currentStep = '1';
let isRecording = false;
let currentAudio = null;
let audioEnabled = true; // Globaler Audio-Schalter

// ----- Aufnahme starten -----
function startRecording() {
  navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    mediaRecorder.start();

    document.getElementById('mic-status').innerText = '🎤 Mikrofon: AN';
    document.getElementById('mic-status').style.color = 'green';

    mediaRecorder.addEventListener("dataavailable", event => {
      audioChunks.push(event.data);
    });
  });
}

// ----- Aufnahme stoppen -----
function stopRecording() {
  if (!mediaRecorder) return;
  mediaRecorder.stop();

  document.getElementById('mic-status').innerText = '🎤 Mikrofon: AUS';
  document.getElementById('mic-status').style.color = 'darkred';

  mediaRecorder.addEventListener("stop", () => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    let formData = new FormData();
    formData.append("audio", audioBlob, "audio.wav");

    const model = getSelectedModel();
    document.getElementById('processing').style.display = 'block';

    fetch(`/transcribe?model=${model}`, {
      method: 'POST',
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        addToChat("Du (Sprache): " + data.transcript);
        return fetch(`/chat-response?model=${model}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_input: data.transcript, current_step: currentStep })
        });
      })
      .then(res => res.json())
      .then(data => {
        addToChat("DIANA: " + data.gpt_response);
        currentStep = data.next_step;

        const ttsToggle = document.getElementById('tts-toggle');
        if (ttsToggle && ttsToggle.checked && audioEnabled) {
          playStreamedAudio(data.gpt_response, getSelectedVoice());
        }
      })
      .catch(err => console.error("Fehler:", err))
      .finally(() => {
        document.getElementById('processing').style.display = 'none';
      });
  });
}

// ----- Aufnahme-Button umschalten -----
function toggleRecording() {
  const btn = document.getElementById('recordButton');
  if (!isRecording) {
    startRecording();
    isRecording = true;
    btn.innerText = "⏹️ Aufnahme stoppen";
  } else {
    stopRecording();
    isRecording = false;
    btn.innerText = "🎤 Spracheingabe starten";
  }
}

// ----- Texteingabe absenden -----
function sendText() {
  const userText = document.getElementById('userText').value;
  const model = getSelectedModel();
  const voice = getSelectedVoice();

  document.getElementById('processing').style.display = 'block';

  fetch(`/chat-response?model=${model}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userText, current_step: currentStep })
  })
    .then(res => res.json())
    .then(data => {
      addToChat("Du: " + userText);
      addToChat("DIANA: " + data.gpt_response);
      currentStep = data.next_step;

      const ttsToggle = document.getElementById('tts-toggle');
      const voice = getSelectedVoice();

      if (!ttsToggle) {
        console.warn("⚠️ Kein TTS-Schalter gefunden.");
      } else if (!ttsToggle.checked) {
        console.log("🔇 Text-to-Speech deaktiviert.");
      } else if (!audioEnabled) {
        console.log("🔕 Audio global deaktiviert.");
      } else {
        console.log("✅ Bedingungen erfüllt – TTS wird ausgeführt.");
        playStreamedAudio(data.gpt_response, voice);
      }

    })
    .catch(err => console.error("Fehler:", err))
    .finally(() => {
      document.getElementById('processing').style.display = 'none';
    });
}

// ----- Chatbox aktualisieren -----
function addToChat(message) {
  const box = document.getElementById('chatbox');
  box.innerHTML += `<div>${message}</div>`;
  box.scrollTop = box.scrollHeight;
}

// ----- Text als Sprache streamen -----
function playStreamedAudio(text, voice) {
  console.log("🟢 playStreamedAudio() aufgerufen mit Stimme:", voice);

  fetch('/tts-stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: text, voice: voice })
  })
  .then(res => res.blob())
  .then(blob => {
    const url = URL.createObjectURL(blob);
    if (currentAudio) currentAudio.pause();
    currentAudio = new Audio(url);
    currentAudio.play();
    console.log("🎧 Audio wird abgespielt.");
  })
  .catch(err => {
    console.error("❌ Fehler beim Abspielen:", err);
  });
}


// ----- Vorlesen abbrechen -----
function stopAudio() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
  }
}

// ----- Audio dauerhaft aktivieren/deaktivieren -----
function toggleAudioEnabled() {
  audioEnabled = !audioEnabled;
  const btn = document.getElementById('toggle-audio');
  if (btn) {
    btn.innerText = audioEnabled ? "🔊 Audio deaktivieren" : "🔇 Audio aktivieren";
  }
}

// ----- Eingabe auch per ENTER absenden -----
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('userText');
  if (input) {
    input.addEventListener('keypress', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendText();
      }
    });
  }
});

// ----- Modell- & Stimmauswahl abrufen -----
function getSelectedModel() {
  const dropdown = document.getElementById('model');
  return dropdown ? dropdown.value : "gpt-4-turbo";
}

function getSelectedVoice() {
  const dropdown = document.getElementById('voice');
  return dropdown ? dropdown.value : "nova";
}
