// Enhanced Voice Agent Script - Professional UI
let isRecording = false;
let isProcessing = false;
let mediaRecorder;
let recordedChunks = [];
let recordingTimer;
let startTime;
let currentSessionId = null;
let isConversationActive = true;

// Error handling configuration
const ERROR_CONFIG = {
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 2000,
  TIMEOUT_MS: 30000,
  
  RETRYABLE_ERRORS: [
    'NETWORK_ERROR',
    'TIMEOUT_ERROR',
    'GENERAL_ERROR'
  ],
  
  ERROR_MESSAGES: {
    'STT_ERROR': 'Speech recognition failed',
    'LLM_ERROR': 'AI processing failed',
    'TTS_ERROR': 'Audio generation failed',
    'NETWORK_ERROR': 'Network connection failed',
    'AUTH_ERROR': 'Authentication failed',
    'QUOTA_ERROR': 'Daily limit reached',
    'TIMEOUT_ERROR': 'Request timed out',
    'GENERAL_ERROR': 'Something went wrong'
  }
};

// DOM Elements
const elements = {
  recordBtn: document.getElementById('main-record-btn'),
  recordIcon: document.getElementById('record-icon'),
  recordStatus: document.getElementById('record-status'),
  recordingTimer: document.getElementById('recording-timer'),
  conversationDisplay: document.getElementById('conversation-display'),
  conversationText: document.getElementById('conversation-text'),
  conversationMeta: document.getElementById('conversation-meta'),
  statusMessage: document.getElementById('status-message'),
  sessionDisplay: document.getElementById('session-display'),
  aiAudio: document.getElementById('ai-response-audio'),
  newSessionBtn: document.getElementById('new-session-btn'),
  copyBtn: document.getElementById('copy-conversation-btn'),
  clearBtn: document.getElementById('clear-conversation-btn'),
  toggleBtn: document.getElementById('toggle-conversation-btn'),
  toggleIcon: document.getElementById('toggle-icon')
};

// Session Management
function getOrCreateSessionId() {
  const urlParams = new URLSearchParams(window.location.search);
  let sessionId = urlParams.get('session_id');
  
  if (!sessionId) {
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    urlParams.set('session_id', sessionId);
    const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
    window.history.replaceState({}, '', newUrl);
    console.log(`Generated new session ID: ${sessionId}`);
  } else {
    console.log(`Using existing session ID: ${sessionId}`);
  }
  
  return sessionId;
}

function updateSessionDisplay() {
  if (elements.sessionDisplay && currentSessionId) {
    elements.sessionDisplay.textContent = currentSessionId;
  }
}

function createNewSession() {
  const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  
  const urlParams = new URLSearchParams(window.location.search);
  urlParams.set('session_id', newSessionId);
  const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
  window.history.pushState({}, '', newUrl);
  
  currentSessionId = newSessionId;
  updateSessionDisplay();
  
  // Clear conversation display
  hideConversation();
  
  console.log(`Created new session: ${newSessionId}`);
  showStatus("New chat session started!", "success");
}

// UI State Management
function updateRecordButtonState(state) {
  elements.recordBtn.classList.remove('recording', 'processing');
  elements.recordingTimer.classList.remove('visible');
  
  switch (state) {
    case 'idle':
      // Use microphone SVG
      elements.recordIcon.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
          <line x1="12" y1="19" x2="12" y2="22"></line>
        </svg>
      `;
      elements.recordStatus.textContent = 'Tap to start conversation';
      break;
    case 'recording':
      elements.recordBtn.classList.add('recording');
      // Use stop SVG
      elements.recordIcon.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="6" y="6" width="12" height="12" rx="2" ry="2"></rect>
        </svg>
      `;
      elements.recordStatus.innerHTML = 'Recording... <span style="color: var(--color-recording-solid)">●</span>';
      elements.recordingTimer.classList.add('visible');
      break;
    case 'processing':
      elements.recordBtn.classList.add('processing');
      // Use processing SVG
      elements.recordIcon.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
      `;
      elements.recordStatus.textContent = 'Processing with AI...';
      break;
  }
}

function showStatus(message, type = 'loading', duration = 0) {
  elements.statusMessage.className = `status-message ${type}`;
  
  if (type === 'loading') {
    elements.statusMessage.innerHTML = `<div class="spinner"></div> ${message}`;
  } else {
    elements.statusMessage.innerHTML = message;
  }
  
  elements.statusMessage.classList.add('visible');
  
  if (duration > 0) {
    setTimeout(() => hideStatus(), duration);
  } else if (type === 'error') {
    setTimeout(() => hideStatus(), 5000);
  }
}

function hideStatus() {
  elements.statusMessage.classList.remove('visible');
}

function showConversation(userText, aiResponse, metadata = {}) {
  const displayText = `You: "${userText}"\n\nAI: ${aiResponse}`;
  elements.conversationText.textContent = displayText;
  
  // Update metadata
  let metaText = `Session: ${currentSessionId}`;
  if (metadata.messageCount) metaText += ` • Messages: ${metadata.messageCount}`;
  if (metadata.model) metaText += ` • Model: ${metadata.model}`;
  if (metadata.isFallback) metaText += ` • Fallback Mode`;
  
  elements.conversationMeta.textContent = metaText;
  elements.conversationDisplay.classList.add('visible');
}

function hideConversation() {
  elements.conversationDisplay.classList.remove('visible');
  elements.conversationText.textContent = '';
  elements.conversationMeta.textContent = '';
}

function updateTimer() {
  if (!isRecording) return;

  const elapsed = Math.floor((Date.now() - startTime) / 1000);
  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  
  elements.recordingTimer.textContent = 
    `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

  // Auto-stop after 5 minutes
  if (elapsed >= 300) {
    stopRecording();
    showStatus("Recording stopped automatically after 5 minutes.", "error");
  }
}

// Error Handling Functions
function parseErrorResponse(response, data) {
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
  let message = `${ERROR_CONFIG.ERROR_MESSAGES[errorInfo.type] || 'Error'}: ${errorInfo.message}`;
  
  if (errorInfo.retryable) {
    message += '<br>This error can be retried automatically.';
  }
  
  if (errorInfo.suggestion) {
    message += `<br>${errorInfo.suggestion}`;
  }
  
  return message;
}

async function retryWithBackoff(asyncFunction, maxRetries = ERROR_CONFIG.MAX_RETRIES) {
  let lastError = null;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const result = await asyncFunction();
      if (attempt > 1) {
        console.log(`Retry successful on attempt ${attempt}`);
      }
      return result;
    } catch (error) {
      lastError = error;
      console.warn(`Attempt ${attempt} failed:`, error.message);
      
      if (error.errorInfo && !error.errorInfo.retryable) {
        console.log(`Error type '${error.errorInfo.type}' is not retryable`);
        throw error;
      }
      
      if (attempt < maxRetries) {
        const delay = ERROR_CONFIG.RETRY_DELAY_MS * Math.pow(1.5, attempt - 1);
        console.log(`Waiting ${delay}ms before retry...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  console.error(`All ${maxRetries} retry attempts failed`);
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

// Recording Functions
async function startRecording() {
  if (isRecording || isProcessing) return;

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 44100
      } 
    });

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
      stream.getTracks().forEach(track => track.stop());
      
      const blob = new Blob(recordedChunks, { type: 'audio/webm' });
      
      isProcessing = true;
      updateRecordButtonState('processing');
      showStatus("Processing with AI...", 'loading');
      
      await queryLLMWithAudio(blob);
    };

    mediaRecorder.onerror = (event) => {
      console.error("MediaRecorder error:", event.error);
      showStatus("Recording error occurred.", "error");
      updateRecordButtonState('idle');
    };

    mediaRecorder.start(1000);
    isRecording = true;
    startTime = Date.now();

    updateRecordButtonState('recording');
    recordingTimer = setInterval(updateTimer, 1000);
    showStatus("Recording started! Speak into your microphone.", "loading");

  } catch (error) {
    console.error("Error accessing microphone:", error);
    
    let errorMessage = "";
    if (error.name === "NotAllowedError") {
      errorMessage = "Microphone access denied. Please allow microphone access and try again.";
    } else if (error.name === "NotFoundError") {
      errorMessage = "No microphone found. Please connect a microphone and try again.";
    } else {
      errorMessage = "Failed to access microphone. Please check your device settings.";
    }
    
    showStatus(errorMessage, "error");
    updateRecordButtonState('idle');
  }
}

function stopRecording() {
  if (!isRecording || !mediaRecorder) return;

  mediaRecorder.stop();
  isRecording = false;
  clearInterval(recordingTimer);
}

// AI Integration
async function queryLLMWithAudio(blob) {
  const sessionId = getOrCreateSessionId();

  try {
    const result = await retryWithBackoff(async () => {
      showStatus("Transcribing → AI thinking → Generating voice...", 'loading');

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

      let data = {};
      try {
        data = await response.json();
      } catch (jsonError) {
        console.warn("Failed to parse JSON response:", jsonError);
      }

      if (!response.ok) {
        const errorInfo = parseErrorResponse(response, data);
        const error = new Error(errorInfo.message);
        error.errorInfo = errorInfo;
        throw error;
      }

      return data;
    });

    // Handle response
    let statusMessage = "";
    let statusType = "success";

    if (result.is_fallback) {
      const errorInfo = parseErrorResponse(null, result);
      statusMessage = `${ERROR_CONFIG.ERROR_MESSAGES[result.error_type] || 'Service degradation'}. Fallback response provided.`;
      statusType = "error";
    } else if (result.error_type === "TTS_ERROR" || result.tts_error) {
      statusMessage = "Audio generation failed. Showing text response only.";
      statusType = "error";
    }

    // Show conversation
    if (result.transcription && result.llm_response) {
      const metadata = {
        messageCount: result.message_count,
        model: result.model,
        isFallback: result.is_fallback
      };
      showConversation(result.transcription, result.llm_response, metadata);
    }

    // Handle audio playback
    if (result.audio_url) {
      elements.aiAudio.src = result.audio_url;
      setupAudioListeners();

      try {
        await elements.aiAudio.play();
        showStatus(statusMessage || "AI response ready! Playing now...", statusType);
      } catch (playErr) {
        console.warn("Autoplay blocked:", playErr);
        showStatus(statusMessage || "AI response ready! Audio loaded.", statusType);
      }
    } else {
      if (!statusMessage) {
        statusMessage = "Response ready! Text-only mode.";
        statusType = "success";
      }
      
      showStatus(statusMessage, statusType);
      
      // Auto-start recording after delay if conversation is active
      if (isConversationActive) {
        setTimeout(() => {
          if (!isRecording && isConversationActive) {
            showStatus("Ready for your response! Recording automatically...", "loading");
            startRecording();
          }
        }, 2000);
      }
    }
    
  } catch (error) {
    console.error("Chat query failed:", error);
    
    if (error.errorInfo) {
      const message = formatErrorMessage(error.errorInfo);
      showStatus(message, "error");
    } else {
      showStatus(`AI query failed: ${error.message}`, "error");
    }
  } finally {
    isProcessing = false;
    updateRecordButtonState('idle');
  }
}

function setupAudioListeners() {
  elements.aiAudio.onended = () => {
    console.log("AI audio finished playing");
    showStatus("Playback completed!", "success", 2000);
    
    // Auto-start recording after AI response if conversation is active
    if (isConversationActive && !isRecording) {
      setTimeout(() => {
        if (!isRecording && isConversationActive) {
          showStatus("Ready for your response! Recording automatically...", "loading");
          startRecording();
        }
      }, 1000);
    }
  };

  elements.aiAudio.onerror = (e) => {
    console.error("Audio playback error:", e);
    showStatus("Error playing audio.", "error");
  };
}

// Control Functions
function toggleConversation() {
  isConversationActive = !isConversationActive;
  
  if (isRecording && !isConversationActive) {
    stopRecording();
  }
  
  const btn = elements.toggleBtn;
  if (isConversationActive) {
    btn.innerHTML = `
      <svg id="toggle-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <rect x="9" y="9" width="6" height="6"></rect>
      </svg>
      Pause Auto-Record
    `;
    btn.className = 'control-btn success';
    showStatus("Conversation resumed. Auto-recording enabled.", "success", 3000);
  } else {
    btn.innerHTML = `
      <svg id="toggle-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <polygon points="10 8 16 12 10 16 10 8"></polygon>
      </svg>
      Resume Auto-Record
    `;
    btn.className = 'control-btn';
    showStatus("Conversation paused. Manual recording only.", "success", 3000);
  }
}

function copyConversation() {
  const text = elements.conversationText.textContent.trim();
  if (text) {
    navigator.clipboard.writeText(text)
      .then(() => showStatus("Conversation copied to clipboard!", "success", 3000))
      .catch(() => showStatus("Failed to copy conversation.", "error"));
  } else {
    showStatus("No conversation to copy.", "error", 3000);
  }
}

function clearConversation() {
  hideConversation();
  showStatus("Conversation cleared.", "success", 2000);
}

// Event Listeners
function setupEventListeners() {
  // Main record button
  elements.recordBtn.addEventListener('click', () => {
    if (isRecording) {
      stopRecording();
    } else if (!isProcessing) {
      startRecording();
    }
  });

  // Control buttons
  elements.newSessionBtn.addEventListener('click', createNewSession);
  elements.copyBtn.addEventListener('click', copyConversation);
  elements.clearBtn.addEventListener('click', clearConversation);
  elements.toggleBtn.addEventListener('click', toggleConversation);

  // Keyboard shortcuts
  document.addEventListener('keydown', (event) => {
    // Space to start/stop recording
    if (event.code === 'Space' && !event.ctrlKey && !event.metaKey) {
      event.preventDefault();
      if (isRecording) {
        stopRecording();
      } else if (!isProcessing) {
        startRecording();
      }
    }

    // Ctrl+C to copy conversation
    if ((event.ctrlKey || event.metaKey) && event.key === 'c') {
      if (elements.conversationDisplay.classList.contains('visible')) {
        event.preventDefault();
        copyConversation();
      }
    }

    // Ctrl+N for new session
    if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
      event.preventDefault();
      createNewSession();
    }

    // Escape to clear status
    if (event.key === 'Escape') {
      hideStatus();
    }
  });

  // Page visibility change
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && elements.aiAudio && !elements.aiAudio.paused) {
      elements.aiAudio.pause();
    }
  });
}

// Initialization
function initialize() {
  console.log("AI Voice Agent initialized");
  
  // Initialize session
  currentSessionId = getOrCreateSessionId();
  updateSessionDisplay();
  
  // Check microphone support
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showStatus("Your browser doesn't support audio recording.", "error");
    elements.recordBtn.disabled = true;
    return;
  }
  
  // Setup event listeners
  setupEventListeners();
  
  // Initial UI state
  updateRecordButtonState('idle');
  
  console.log(`Initialized with session ID: ${currentSessionId}`);
}

// Start the application
document.addEventListener('DOMContentLoaded', initialize);
