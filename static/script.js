// Voice Agent Script
let isGenerating = false;

async function generateAudio() {
  if (isGenerating) return;

  const textInput = document.getElementById("text-input");
  const status = document.getElementById("status");
  const audioPlayer = document.getElementById("audio-player");
  const generateBtn = document.getElementById("generate-btn");
  const btnIcon = document.getElementById("btn-icon");
  const btnText = document.getElementById("btn-text");

  const text = textInput.value.trim();

  // Input validation
  if (!text) {
    showStatus("❗ Please enter some text to convert to speech.", "error");
    focusInput();
    return;
  }

  if (text.length > 5000) {
    showStatus("❗ Text is too long. Please keep it under 5000 characters.", "error");
    focusInput();
    return;
  }

  // Start generation process
  isGenerating = true;
  generateBtn.disabled = true;
  audioPlayer.style.display = "none";
  
  // Update button to loading state
  btnIcon.innerHTML = '<div class="spinner"></div>';
  btnText.textContent = "Generating...";

  showStatus("Generating audio... This may take a moment.", "loading");

  try {
    const response = await fetch("/generate-audio", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        text: text,
        voiceId: "en-US-natalie"
      })
    });

    // Check if response is ok
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.audio_url) {
      // Success - setup audio player
      audioPlayer.src = data.audio_url;
      audioPlayer.style.display = "block";
      
      // Setup audio event listeners
      setupAudioListeners(audioPlayer);
      
      // Auto-play the audio
      try {
        await audioPlayer.play();
        showStatus("Audio generated successfully! Playing now...", "success");
      } catch (playError) {
        console.warn("Auto-play failed:", playError);
        showStatus("Audio generated successfully! Click play to listen.", "success");
      }
      
    } else {
      throw new Error(data.error || "No audio URL received from server");
    }

  } catch (error) {
    console.error("Generation error:", error);
    
    // Handle different types of errors
    let errorMessage = "❌ ";
    if (error.name === "TypeError" && error.message.includes("fetch")) {
      errorMessage += "Network error. Please check your connection and try again.";
    } else if (error.message.includes("HTTP error")) {
      errorMessage += "Server error. Please try again later.";
    } else {
      errorMessage += error.message || "Failed to generate audio. Please try again.";
    }
    
    showStatus(errorMessage, "error");
    
  } finally {
    // Reset button state
    isGenerating = false;
    generateBtn.disabled = false;
    btnIcon.textContent = "🎵";
    btnText.textContent = "Generate Voice";
  }
}

function setupAudioListeners(audioPlayer) {
  // Remove existing listeners to prevent duplicates
  audioPlayer.onplay = null;
  audioPlayer.onpause = null;
  audioPlayer.onended = null;
  audioPlayer.onerror = null;

  audioPlayer.onplay = () => {
    console.log("Audio started playing");
  };

  audioPlayer.onpause = () => {
    console.log("Audio paused");
  };

  audioPlayer.onended = () => {
    console.log("Audio finished playing");
    showStatus("Playback completed!", "success");
  };

  audioPlayer.onerror = (e) => {
    console.error("Audio playback error:", e);
    showStatus("Error playing audio. Please try generating again.", "error");
  };

  audioPlayer.onloadstart = () => {
    console.log("Audio loading started");
  };

  audioPlayer.oncanplay = () => {
    console.log("Audio can start playing");
  };
}

function showStatus(message, type, statusElement = null) {
  const status = statusElement || document.getElementById("status");
  
  // Hide current status
  status.classList.remove("show");
  
  setTimeout(() => {
    status.textContent = message;
    status.className = `status ${type}`;
    status.classList.add("show");
    
    // Auto-hide error messages after 5 seconds
    if (type === "error") {
      setTimeout(() => {
        hideStatus(status);
      }, 5000);
    }
  }, 100);
}

function hideStatus(statusElement = null) {
  const status = statusElement || document.getElementById("status");
  status.classList.remove("show");
}

function focusInput() {
  const textInput = document.getElementById("text-input");
  textInput.focus();
}

// Echo Bot Functionality
let mediaRecorder;
let recordedChunks = [];
let isRecording = false;
let recordingTimer;
let startTime;

async function startRecording() {
  if (isRecording) return;

  const startBtn = document.getElementById("start-record-btn");
  const stopBtn = document.getElementById("stop-record-btn");
  const echoStatus = document.getElementById("echo-status");
  const timer = document.getElementById("timer");
  const startIcon = document.getElementById("start-record-icon");
  const startText = document.getElementById("start-record-text");
  const recordedAudio = document.getElementById("recorded-audio");
  const transcriptionResult = document.getElementById("transcription-result");

  try {
    // Request microphone access
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 44100
      } 
    });

    // Initialize MediaRecorder
    mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus'
    });

    recordedChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        recordedChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      // Create blob from recorded chunks
      const blob = new Blob(recordedChunks, { type: 'audio/webm' });
      const audioUrl = URL.createObjectURL(blob);
      
      // Set up audio player
      recordedAudio.src = audioUrl;
      recordedAudio.style.display = "block";
      
      // Stop all tracks to release microphone
      stream.getTracks().forEach(track => track.stop());
      
      showStatus("Recording completed! Processing transcription...", "success", echoStatus);
      
      // Transcribe the recording
      await transcribeAudio(blob);
    };

    mediaRecorder.onerror = (event) => {
      console.error("MediaRecorder error:", event.error);
      showStatus("Recording error occurred.", "error", echoStatus);
    };

    // Start recording
    mediaRecorder.start(1000); // Collect data every second
    isRecording = true;
    startTime = Date.now();

    // Update UI
    startBtn.disabled = true;
    stopBtn.disabled = false;
    startBtn.classList.add("recording");
    startText.textContent = "Recording...";
    timer.style.display = "block";
    recordedAudio.style.display = "none";
    
    // Hide previous transcription
    if (transcriptionResult) {
      transcriptionResult.style.display = "none";
    }

    // Start timer
    recordingTimer = setInterval(updateTimer, 1000);

    showStatus("Recording started! Speak into your microphone.", "loading", echoStatus);

  } catch (error) {
    console.error("Error accessing microphone:", error);
    
    let errorMessage = "❌ ";
    if (error.name === "NotAllowedError") {
      errorMessage += "Microphone access denied. Please allow microphone access and try again.";
    } else if (error.name === "NotFoundError") {
      errorMessage += "No microphone found. Please connect a microphone and try again.";
    } else {
      errorMessage += "Failed to access microphone. Please check your device settings.";
    }
    
    showStatus(errorMessage, "error", echoStatus);
  }
}

// Transcribe audio using the server endpoint
async function transcribeAudio(blob) {
  const echoStatus = document.getElementById("echo-status");
  const transcriptionResult = document.getElementById("transcription-result");
  const transcriptionText = document.getElementById("transcription-text");
  
  const formData = new FormData();
  
  // Create a unique filename with timestamp
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `recording_${timestamp}.webm`;
  
  formData.append("file", blob, filename);

  showStatus("Transcribing audio... Please wait.", "loading", echoStatus);

  try {
    const response = await fetch("/transcribe/file", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `Transcription failed with status: ${response.status}`);
    }

    const data = await response.json();

    if (data.transcription) {
      // Display the transcription
      transcriptionText.textContent = data.transcription;
      transcriptionResult.style.display = "block";
      
      // Show success message with additional info
      let successMessage = "Transcription completed!";
      if (data.audio_duration) {
        successMessage += ` (Duration: ${Math.round(data.audio_duration)}s)`;
      }
      
      showStatus(successMessage, "success", echoStatus);
      console.log("Transcription result:", data);
    } else {
      throw new Error("No transcription received from server");
    }

  } catch (err) {
    console.error("Transcription failed:", err);
    showStatus(`Transcription failed: ${err.message}`, "error", echoStatus);
    
    // Hide transcription result on error
    if (transcriptionResult) {
      transcriptionResult.style.display = "none";
    }
  }
}

function stopRecording() {
  if (!isRecording || !mediaRecorder) return;

  const startBtn = document.getElementById("start-record-btn");
  const stopBtn = document.getElementById("stop-record-btn");
  const timer = document.getElementById("timer");
  const startIcon = document.getElementById("start-record-icon");
  const startText = document.getElementById("start-record-text");

  // Stop recording
  mediaRecorder.stop();
  isRecording = false;

  // Stop timer
  clearInterval(recordingTimer);

  // Reset UI
  startBtn.disabled = false;
  stopBtn.disabled = true;
  startBtn.classList.remove("recording");
  startIcon.textContent = "🎙️";
  startText.textContent = "Start Recording";
  timer.style.display = "none";
  timer.textContent = "00:00";
}

function updateTimer() {
  if (!isRecording) return;

  const elapsed = Math.floor((Date.now() - startTime) / 1000);
  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  
  document.getElementById("timer").textContent = 
    `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

  // Auto-stop after 5 minutes
  if (elapsed >= 300) {
    stopRecording();
    showStatus("Recording stopped automatically after 5 minutes.", "loading", document.getElementById("echo-status"));
  }
}

// Copy transcription to clipboard
function copyTranscription() {
  const transcriptionText = document.getElementById("transcription-text");
  const echoStatus = document.getElementById("echo-status");
  
  if (transcriptionText && transcriptionText.textContent.trim()) {
    navigator.clipboard.writeText(transcriptionText.textContent.trim())
      .then(() => {
        showStatus("📋 Transcription copied to clipboard!", "success", echoStatus);
      })
      .catch((err) => {
        console.error("Failed to copy text:", err);
        showStatus("Failed to copy transcription.", "error", echoStatus);
      });
  }
}

// Clear transcription
function clearTranscription() {
  const transcriptionResult = document.getElementById("transcription-result");
  const transcriptionText = document.getElementById("transcription-text");
  const echoStatus = document.getElementById("echo-status");
  
  if (transcriptionResult) {
    transcriptionResult.style.display = "none";
  }
  if (transcriptionText) {
    transcriptionText.textContent = "";
  }
  
  showStatus("Transcription cleared.", "success", echoStatus);
}

// Keyboard shortcuts
document.addEventListener("keydown", function(event) {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    generateAudio();
  }
  
  // Escape to clear status
  if (event.key === "Escape") {
    hideStatus();
    hideStatus(document.getElementById("echo-status"));
  }

  // Space to start/stop recording (when not focused on text input)
  if (event.code === "Space" && document.activeElement !== document.getElementById("text-input")) {
    event.preventDefault();
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }

  // Ctrl+C to copy transcription
  if ((event.ctrlKey || event.metaKey) && event.key === "c" && 
      document.getElementById("transcription-result") && 
      document.getElementById("transcription-result").style.display !== "none") {
    if (document.activeElement !== document.getElementById("text-input")) {
      event.preventDefault();
      copyTranscription();
    }
  }
});

document.getElementById("text-input").addEventListener("input", function(event) {
  const text = event.target.value;
  const length = text.length;
  
  // Update character counter
  const charCounter = document.getElementById("char-counter");
  if (charCounter) {
    charCounter.textContent = `${length}/5000`;
  }
  
  if (length > 4000) {
    const remaining = 5000 - length;
    if (remaining > 0) {
      showStatus(`⚠️ ${remaining} characters remaining`, "loading");
    } else {
      showStatus("❗ Text is too long! Please reduce it.", "error");
    }
  } else if (length > 0) {
    hideStatus();
  }
});

// Auto-resize textarea
document.getElementById("text-input").addEventListener("input", function() {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 200) + 'px';
});

// Initialize on page load
document.addEventListener("DOMContentLoaded", function() {
  console.log("Voice Agent with Echo Bot and Transcription initialized");
  
  // Focus on text input
  focusInput();
  
  // Add event listeners for buttons
  document.getElementById("generate-btn").addEventListener("click", generateAudio);
  document.getElementById("start-record-btn").addEventListener("click", startRecording);
  document.getElementById("stop-record-btn").addEventListener("click", stopRecording);
  
  // Add event listeners for transcription buttons (if they exist)
  const copyBtn = document.getElementById("copy-transcription-btn");
  const clearBtn = document.getElementById("clear-transcription-btn");
  
  if (copyBtn) {
    copyBtn.addEventListener("click", copyTranscription);
  }
  if (clearBtn) {
    clearBtn.addEventListener("click", clearTranscription);
  }
  
  // Check for MediaRecorder support
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showStatus("❌ Your browser doesn't support audio recording.", "error", document.getElementById("echo-status"));
    document.getElementById("start-record-btn").disabled = true;
  }
  
  // Add some example text if empty
  const textInput = document.getElementById("text-input");
  if (!textInput.value.trim()) {
    // Optional: Add example text
    // textInput.value = "Hello! This is a test of the AI voice generation system.";
  }
});

// Handle page visibility change (pause audio when tab is hidden)
document.addEventListener("visibilitychange", function() {
  if (document.hidden) {
    const audioPlayer = document.getElementById("audio-player");
    const recordedAudio = document.getElementById("recorded-audio");
    
    if (audioPlayer && !audioPlayer.paused) {
      audioPlayer.pause();
    }
    if (recordedAudio && !recordedAudio.paused) {
      recordedAudio.pause();
    }
  }
});

// Utility function to format time
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Export functions for potential external use
window.voiceAgent = {
  generateAudio,
  showStatus,
  hideStatus,
  startRecording,
  stopRecording,
  transcribeAudio,
  copyTranscription,
  clearTranscription
};