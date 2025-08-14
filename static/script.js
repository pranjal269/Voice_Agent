// Voice Agent Script
let isGenerating = false;

// Error handling and retry configuration
const ERROR_CONFIG = {
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 2000,
  TIMEOUT_MS: 30000,
  
  // Error types that can be retried
  RETRYABLE_ERRORS: [
    'NETWORK_ERROR',
    'TIMEOUT_ERROR',
    'GENERAL_ERROR'
  ],
  
  // User-friendly error messages
  ERROR_MESSAGES: {
    'STT_ERROR': '🎤 Speech recognition failed',
    'LLM_ERROR': '🤖 AI processing failed',
    'TTS_ERROR': '🔊 Audio generation failed',
    'NETWORK_ERROR': '🌐 Network connection failed',
    'AUTH_ERROR': '🔑 Authentication failed',
    'QUOTA_ERROR': '📊 Daily limit reached',
    'TIMEOUT_ERROR': '⏱️ Request timed out',
    'GENERAL_ERROR': '⚠️ Something went wrong'
  }
};

// Session management
let currentSessionId = null;

// Conversation control
let isConversationActive = true;

// Get or create session ID from URL params
function getOrCreateSessionId() {
  const urlParams = new URLSearchParams(window.location.search);
  let sessionId = urlParams.get('session_id');
  
  if (!sessionId) {
    // Generate a new session ID
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    
    // Update URL with new session ID
    urlParams.set('session_id', sessionId);
    const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
    window.history.replaceState({}, '', newUrl);
    
    console.log(`Generated new session ID: ${sessionId}`);
  } else {
    console.log(`Using existing session ID: ${sessionId}`);
  }
  
  return sessionId;
}

// Update session display in UI
function updateSessionDisplay() {
  const sessionDisplay = document.getElementById("session-display");
  if (sessionDisplay && currentSessionId) {
    sessionDisplay.textContent = `Session: ${currentSessionId}`;
  }
}

// Create new chat session
function createNewSession() {
  // Generate new session ID
  const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  
  // Update URL
  const urlParams = new URLSearchParams(window.location.search);
  urlParams.set('session_id', newSessionId);
  const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
  window.history.pushState({}, '', newUrl);
  
  // Update current session
  currentSessionId = newSessionId;
  updateSessionDisplay();
  
  // Clear UI
  const transcriptionResult = document.getElementById("transcription-result");
  const transcriptionText = document.getElementById("transcription-text");
  const recordedAudio = document.getElementById("recorded-audio");
  const echoStatus = document.getElementById("echo-status");
  
  if (transcriptionResult) transcriptionResult.style.display = "none";
  if (transcriptionText) transcriptionText.textContent = "";
  if (recordedAudio) recordedAudio.style.display = "none";
  if (echoStatus) hideStatus(echoStatus);
  
  console.log(`Created new session: ${newSessionId}`);
  showStatus("New chat session started!", "success", document.getElementById("echo-status"));
}

// Stop the conversation (disable auto-recording)
function stopConversation() {
  isConversationActive = false;
  
  // Stop any ongoing recording
  if (isRecording) {
    stopRecording();
  }
  
  // Update UI buttons
  updateConversationControls();
  
  console.log("Conversation stopped");
  showStatus("Conversation stopped. You can still record manually or click 'Resume Conversation'.", "success", document.getElementById("echo-status"));
}

// Resume the conversation (re-enable auto-recording)
function resumeConversation() {
  isConversationActive = true;
  
  // Update UI buttons
  updateConversationControls();
  
  console.log("Conversation resumed");
  showStatus("Conversation resumed. Auto-recording will start after AI responses.", "success", document.getElementById("echo-status"));
}

// Update conversation control buttons
function updateConversationControls() {
  const stopBtn = document.getElementById("stop-conversation-btn");
  const resumeBtn = document.getElementById("resume-conversation-btn");
  
  if (stopBtn && resumeBtn) {
    if (isConversationActive) {
      stopBtn.style.display = "block";
      resumeBtn.style.display = "none";
    } else {
      stopBtn.style.display = "none";
      resumeBtn.style.display = "block";
    }
  }
}

// Enhanced Error Handling Functions
function parseErrorResponse(response, data) {
  // Try to parse enhanced error response from server
  if (data && data.error_type) {
    return {
      type: data.error_type,
      message: data.error || data.fallback_text || 'Unknown error occurred',
      originalError: data.original_error || null,
      retryable: ERROR_CONFIG.RETRYABLE_ERRORS.includes(data.error_type),
      suggestion: data.retry_suggestion || 'Please try again',
      timestamp: data.timestamp || Date.now()
    };
  }
  
  // Fallback to basic error parsing
  const statusCode = response?.status || 0;
  let errorType = 'GENERAL_ERROR';
  let message = 'An unexpected error occurred';
  
  if (statusCode === 503) {
    errorType = 'NETWORK_ERROR';
    message = 'Service temporarily unavailable';
  } else if (statusCode === 429) {
    errorType = 'QUOTA_ERROR';
    message = 'Too many requests. Please try again later.';
  } else if (statusCode === 401 || statusCode === 403) {
    errorType = 'AUTH_ERROR';
    message = 'Authentication failed';
  } else if (statusCode >= 500) {
    errorType = 'NETWORK_ERROR';
    message = 'Server error occurred';
  }
  
  return {
    type: errorType,
    message: data?.error || message,
    originalError: null,
    retryable: ERROR_CONFIG.RETRYABLE_ERRORS.includes(errorType),
    suggestion: 'Please try again in a moment',
    timestamp: Date.now()
  };
}

function formatErrorMessage(errorInfo) {
  const icon = ERROR_CONFIG.ERROR_MESSAGES[errorInfo.type] || '⚠️';
  let message = `${icon} ${errorInfo.message}`;
  
  if (errorInfo.retryable) {
    message += '\n🔄 This error can be retried automatically.';
  }
  
  if (errorInfo.suggestion) {
    message += `\n💡 ${errorInfo.suggestion}`;
  }
  
  return message;
}

async function retryWithBackoff(asyncFunction, maxRetries = ERROR_CONFIG.MAX_RETRIES) {
  let lastError = null;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const result = await asyncFunction();
      if (attempt > 1) {
        console.log(`✅ Retry successful on attempt ${attempt}`);
      }
      return result;
    } catch (error) {
      lastError = error;
      console.warn(`❌ Attempt ${attempt} failed:`, error.message);
      
      // Don't retry non-retryable errors
      if (error.errorInfo && !error.errorInfo.retryable) {
        console.log(`🚫 Error type '${error.errorInfo.type}' is not retryable`);
        throw error;
      }
      
      // Don't wait after the last attempt
      if (attempt < maxRetries) {
        const delay = ERROR_CONFIG.RETRY_DELAY_MS * Math.pow(1.5, attempt - 1); // Exponential backoff
        console.log(`⏳ Waiting ${delay}ms before retry...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  console.error(`❌ All ${maxRetries} retry attempts failed`);
  throw lastError;
}

async function fetchWithTimeout(url, options, timeoutMs = ERROR_CONFIG.TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      const timeoutError = new Error(`Request timed out after ${timeoutMs}ms`);
      timeoutError.errorInfo = {
        type: 'TIMEOUT_ERROR',
        message: 'Request timed out',
        retryable: true,
        suggestion: 'Please try again with a shorter message'
      };
      throw timeoutError;
    }
    throw error;
  }
}

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

  try {
    const result = await retryWithBackoff(async () => {
      showStatus("Generating audio... This may take a moment.", "loading");
      
      const response = await fetchWithTimeout("/generate-audio", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          text: text,
          voiceId: "en-US-natalie"
        })
      });

      // Parse response data
      let data = {};
      try {
        data = await response.json();
      } catch (jsonError) {
        console.warn("Failed to parse JSON response:", jsonError);
      }

      // Check if response is ok
      if (!response.ok) {
        const errorInfo = parseErrorResponse(response, data);
        const error = new Error(errorInfo.message);
        error.errorInfo = errorInfo;
        throw error;
      }

      return data;
    });

    // Handle successful response
    if (result.audio_url) {
      // Success - setup audio player
      audioPlayer.src = result.audio_url;
      audioPlayer.style.display = "block";
      
      // Setup audio event listeners
      setupAudioListeners(audioPlayer);
      
      // Auto-play the audio
      try {
        await audioPlayer.play();
        showStatus("✅ Audio generated successfully! Playing now...", "success");
      } catch (playError) {
        console.warn("Auto-play failed:", playError);
        showStatus("✅ Audio generated successfully! Click play to listen.", "success");
      }
      
    } else if (result.fallback_text || result.error_type) {
      // Handle service degradation with fallback
      audioPlayer.style.display = "none";
      
      const errorInfo = parseErrorResponse(null, result);
      const message = formatErrorMessage(errorInfo);
      showStatus(message, "error");
      
      // Show fallback text prominently
      if (result.fallback_text) {
        textInput.style.backgroundColor = "rgba(239, 68, 68, 0.1)";
        setTimeout(() => {
          textInput.style.backgroundColor = "";
        }, 3000);
      }
    } else {
      throw new Error(result.error || "No audio URL received from server");
    }

  } catch (error) {
    console.error("Generation error:", error);
    
    if (error.errorInfo) {
      // Use enhanced error info
      const message = formatErrorMessage(error.errorInfo);
      showStatus(message, "error");
    } else {
      // Fallback error handling
      let errorMessage = "❌ ";
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        errorMessage += "Network error. Please check your connection and try again.";
      } else if (error.message.includes("HTTP error")) {
        errorMessage += "Server error. Please try again later.";
      } else {
        errorMessage += error.message || "Failed to generate audio. Please try again.";
      }
      showStatus(errorMessage, "error");
    }
    
  } finally {
    // Reset button state
    isGenerating = false;
    generateBtn.disabled = false;
    btnIcon.textContent = "🎵";
    btnText.textContent = "Generate Voice";
  }
}

function setupAudioListeners(audioPlayer, statusElement = null, autoRecord = false) {
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
    showStatus("Playback completed!", "success", statusElement);
    
    // Auto-start recording after AI response finishes (with a small delay)
    if (autoRecord && !isRecording && isConversationActive) {
      console.log("Auto-starting recording after AI response...");
      setTimeout(() => {
        if (!isRecording && isConversationActive) { // Double-check we're not already recording and conversation is still active
          showStatus("Ready for your response! Recording automatically...", "loading", statusElement);
          startRecording();
        }
      }, 1000); // 1 second delay to give user time to process the response
    } else if (autoRecord && !isConversationActive) {
      showStatus("Conversation stopped. Click 'Resume Conversation' to continue.", "success", statusElement);
    }
  };

  audioPlayer.onerror = (e) => {
    console.error("Audio playback error:", e);
    showStatus("Error playing audio. Please try generating again.", "error", statusElement);
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

      // Stop all tracks to release microphone
      stream.getTracks().forEach(track => track.stop());
      
      showStatus("Recording completed! Processing with AI...", "loading", echoStatus);
      
      // Send to LLM for AI response (transcribe -> LLM -> TTS)
      await queryLLMWithAudio(blob);
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

// Enhanced LLM Query with Audio: Send recording to /agent/chat/{session_id} and play AI response audio
async function queryLLMWithAudio(blob) {
  const echoStatus = document.getElementById("echo-status");
  const recordedAudio = document.getElementById("recorded-audio");
  const transcriptionResult = document.getElementById("transcription-result");
  const transcriptionText = document.getElementById("transcription-text");

  // Get current session ID
  const sessionId = getOrCreateSessionId();

  try {
    const result = await retryWithBackoff(async () => {
      showStatus("🎤 Transcribing → 🤖 AI thinking → 🔊 Generating voice...", "loading", echoStatus);

      const formData = new FormData();
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `recording_${timestamp}.webm`;
      formData.append("file", blob, filename);
      formData.append("model", "gemini-1.5-flash");
      formData.append("temperature", "0.7");
      formData.append("voiceId", "en-US-natalie");

      const response = await fetchWithTimeout(`/agent/chat/${encodeURIComponent(sessionId)}`, {
        method: "POST",
        body: formData,
      });

      // Parse response data
      let data = {};
      try {
        data = await response.json();
      } catch (jsonError) {
        console.warn("Failed to parse JSON response:", jsonError);
      }

      // Check if response is ok
      if (!response.ok) {
        const errorInfo = parseErrorResponse(response, data);
        const error = new Error(errorInfo.message);
        error.errorInfo = errorInfo;
        throw error;
      }

      return data;
    });

    // Handle successful responses with potential service degradation
    let statusMessage = "";
    let statusType = "success";

    if (result.is_fallback) {
      // This is a fallback response from API failures
      const errorInfo = parseErrorResponse(null, result);
      statusMessage = `${ERROR_CONFIG.ERROR_MESSAGES[result.error_type] || '⚠️'} Service degradation. Fallback response: ${result.llm_response}`;
      statusType = "error";
    } else if (result.error_type === "TTS_ERROR") {
      // TTS failed but we have text response
      statusMessage = "🔊 Audio generation failed. Showing text response only.";
      statusType = "error";
    } else if (result.tts_error) {
      // Another form of TTS error
      statusMessage = "🔊 Audio generation had issues. Response displayed as text.";
      statusType = "error";
    }

    // Update transcription UI if provided
    if (result.transcription && transcriptionText && transcriptionResult) {
      let displayText = `You said: "${result.transcription}"\n\nAI Response: ${result.llm_response}`;
      
      // Add error context if this was a fallback
      if (result.is_fallback) {
        displayText += `\n\n⚠️ Note: This was a fallback response due to ${result.error_type}`;
      }
      
      transcriptionText.textContent = displayText;
      transcriptionResult.style.display = "block";
      
      // Show session info in meta
      const metaElement = document.getElementById("transcription-meta");
      if (metaElement) {
        let metaText = `Session: ${sessionId} • Messages: ${result.message_count || 0} • Model: ${result.model || 'gemini-1.5-flash'}`;
        if (result.is_fallback) {
          metaText += ` • Fallback Mode`;
        }
        metaElement.textContent = metaText;
      }
    }

    // Handle audio playback or text-only response
    if (result.audio_url) {
      // Play AI response audio
      recordedAudio.src = result.audio_url;
      recordedAudio.style.display = "block";
      setupAudioListeners(recordedAudio, echoStatus, true); // Pass true for auto-record

      try {
        await recordedAudio.play();
        showStatus(statusMessage || "✅ AI response ready! Playing now...", statusType, echoStatus);
      } catch (playErr) {
        console.warn("Autoplay blocked:", playErr);
        showStatus(statusMessage || "✅ AI response ready! Click play to listen.", statusType, echoStatus);
      }
    } else {
      // Text-only response (TTS failed or fallback)
      recordedAudio.style.display = "none";
      
      if (!statusMessage) {
        statusMessage = "✅ Response ready! Text-only mode. You can record your next message.";
        statusType = "success";
      }
      
      showStatus(statusMessage, statusType, echoStatus);
      
      // Auto-start recording after a delay if conversation is active
      if (isConversationActive && !isRecording) {
        setTimeout(() => {
          if (!isRecording && isConversationActive) {
            showStatus("🎤 Ready for your response! Recording automatically...", "loading", echoStatus);
            startRecording();
          }
        }, 2000); // 2 second delay for text-only responses
      }
    }
    
  } catch (error) {
    console.error("Chat query failed:", error);
    
    if (error.errorInfo) {
      // Use enhanced error info
      const message = formatErrorMessage(error.errorInfo);
      showStatus(message, "error", echoStatus);
      
      // For certain errors, suggest specific actions
      if (error.errorInfo.type === 'QUOTA_ERROR') {
        setTimeout(() => {
          showStatus("💡 Consider upgrading your plan for unlimited conversations!", "loading", echoStatus);
        }, 3000);
      } else if (error.errorInfo.type === 'NETWORK_ERROR') {
        setTimeout(() => {
          showStatus("🔄 Try recording a shorter message or check your internet connection.", "loading", echoStatus);
        }, 3000);
      }
    } else {
      // Fallback error handling
      showStatus(`❌ AI query failed: ${error.message}`, "error", echoStatus);
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

  // Ctrl+Shift+S to stop/resume conversation
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === "S") {
    event.preventDefault();
    if (isConversationActive) {
      stopConversation();
    } else {
      resumeConversation();
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
  
  // Initialize session ID
  currentSessionId = getOrCreateSessionId();
  console.log(`Initialized with session ID: ${currentSessionId}`);
  updateSessionDisplay();
  
  // Focus on text input
  focusInput();
  
  // Add event listeners for buttons
  document.getElementById("generate-btn").addEventListener("click", generateAudio);
  document.getElementById("start-record-btn").addEventListener("click", startRecording);
  document.getElementById("stop-record-btn").addEventListener("click", stopRecording);
  
  // Add event listener for new session button
  const newSessionBtn = document.getElementById("new-session-btn");
  if (newSessionBtn) {
    newSessionBtn.addEventListener("click", createNewSession);
  }
  
  // Add event listeners for conversation control buttons
  const stopConversationBtn = document.getElementById("stop-conversation-btn");
  const resumeConversationBtn = document.getElementById("resume-conversation-btn");
  
  if (stopConversationBtn) {
    stopConversationBtn.addEventListener("click", stopConversation);
  }
  if (resumeConversationBtn) {
    resumeConversationBtn.addEventListener("click", resumeConversation);
  }
  
  // Initialize conversation controls UI
  updateConversationControls();
  
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
  clearTranscription,
  queryLLMWithAudio,
};