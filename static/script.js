// Global variables
let sessionId = generateSessionId();
let currentInputMethod = 'text';
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let studentRegistered = false;

// Generate unique session ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    checkStudentRegistration();
});

// Setup event listeners
function setupEventListeners() {
    // Drag and drop for image upload
    const fileUpload = document.querySelector('.file-upload');
    if (fileUpload) {
        fileUpload.addEventListener('dragover', handleDragOver);
        fileUpload.addEventListener('dragleave', handleDragLeave);
        fileUpload.addEventListener('drop', handleDrop);
    }

    // Enter key for text input
    const textQuery = document.getElementById('textQuery');
    if (textQuery) {
        textQuery.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && e.ctrlKey) {
                submitTextQuery();
            }
        });
    }
}

// Check if student is already registered
function checkStudentRegistration() {
    const savedSession = localStorage.getItem('eduMentorSession');
    if (savedSession) {
        const sessionData = JSON.parse(savedSession);
        sessionId = sessionData.sessionId;
        populateStudentForm(sessionData.studentInfo);
        displayStudentInfo(sessionData.studentInfo);
        studentRegistered = true;
    }
}

// Register student information
async function registerStudent() {
    const name = document.getElementById('studentName').value;
    const studentClass = document.getElementById('studentClass').value;
    const board = document.getElementById('studentBoard').value;
    const language = document.getElementById('languagePreference').value;

    if (!studentClass) {
        showError('Please select your class/level');
        return;
    }

    const studentInfo = {
        name: name,
        class: studentClass,
        board: board,
        language: language
    };

    try {
        const response = await fetch('/api/student/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                ...studentInfo
            })
        });

        const result = await response.json();

        if (result.success) {
            // Save to localStorage
            localStorage.setItem('eduMentorSession', JSON.stringify({
                sessionId: sessionId,
                studentInfo: studentInfo
            }));

            displayStudentInfo(studentInfo);
            studentRegistered = true;
            showSuccess('Student information saved successfully!');
            
            // Clear the response area
            const responseArea = document.getElementById('responseArea');
            responseArea.innerHTML = `
                <div style="text-align: center; color: #48bb78; padding: 2rem;">
                    <i class="fas fa-check-circle" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                    <p>Great! Now you can ask me any question. I'm here to help you learn!</p>
                </div>
            `;
        } else {
            showError(result.error || 'Failed to register student information');
        }
    } catch (error) {
        showError('Network error. Please check your connection.');
        console.error('Registration error:', error);
    }
}

// Display student information
function displayStudentInfo(studentInfo) {
    const display = document.getElementById('studentInfoDisplay');
    const content = document.getElementById('studentInfoContent');
    
    content.innerHTML = `
        <p><strong>Name:</strong> ${studentInfo.name || 'Not provided'}</p>
        <p><strong>Class:</strong> ${studentInfo.class}</p>
        <p><strong>Board:</strong> ${studentInfo.board || 'Not specified'}</p>
        <p><strong>Language:</strong> ${studentInfo.language}</p>
    `;
    
    display.classList.remove('hidden');
}

// Populate student form with saved data
function populateStudentForm(studentInfo) {
    document.getElementById('studentName').value = studentInfo.name || '';
    document.getElementById('studentClass').value = studentInfo.class || '';
    document.getElementById('studentBoard').value = studentInfo.board || '';
    document.getElementById('languagePreference').value = studentInfo.language || 'English';
}

// Switch input method
function switchInputMethod(method) {
    // Update active button
    document.querySelectorAll('.method-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-method="${method}"]`).classList.add('active');

    // Hide all input methods
    document.getElementById('textInput').classList.add('hidden');
    document.getElementById('imageInput').classList.add('hidden');
    document.getElementById('voiceInput').classList.add('hidden');

    // Show selected method
    document.getElementById(`${method}Input`).classList.remove('hidden');
    
    currentInputMethod = method;
}

// Submit text query
async function submitTextQuery() {
    if (!studentRegistered) {
        showError('Please register your student information first');
        return;
    }

    const query = document.getElementById('textQuery').value.trim();
    if (!query) {
        showError('Please enter your question');
        return;
    }

    // Add user message to response area
    addMessage(query, 'user');
    
    // Clear input
    document.getElementById('textQuery').value = '';
    
    // Show loading
    showLoading(true);

    try {
        const response = await fetch('/api/query/text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                query: query
            })
        });

        const result = await response.json();

        if (result.success) {
            addMessage(result.response, 'ai');
        } else {
            showError(result.error || 'Failed to process your question');
        }
    } catch (error) {
        showError('Network error. Please check your connection.');
        console.error('Text query error:', error);
    } finally {
        showLoading(false);
    }
}

// Handle image upload
function handleImageUpload(input) {
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('imagePreview');
            const img = document.getElementById('previewImg');
            img.src = e.target.result;
            preview.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
}

// Submit image query
async function submitImageQuery() {
    if (!studentRegistered) {
        showError('Please register your student information first');
        return;
    }

    const fileInput = document.getElementById('imageFile');
    if (!fileInput.files || !fileInput.files[0]) {
        showError('Please select an image');
        return;
    }

    const file = fileInput.files[0];
    const reader = new FileReader();
    
    reader.onload = async function(e) {
        const imageData = e.target.result;
        
        // Add user message
        addMessage('📸 Image uploaded for analysis', 'user');
        
        // Show loading
        showLoading(true);

        try {
            const response = await fetch('/api/query/image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    image_data: imageData
                })
            });

            const result = await response.json();

            if (result.success) {
                if (result.extracted_text) {
                    addMessage(`Extracted text: "${result.extracted_text}"`, 'extracted-text');
                }
                addMessage(result.response, 'ai');
            } else {
                showError(result.error || 'Failed to process the image');
            }
        } catch (error) {
            showError('Network error. Please check your connection.');
            console.error('Image query error:', error);
        } finally {
            showLoading(false);
        }
    };
    
    reader.readAsDataURL(file);
}

// Start voice recording
async function startRecording() {
    if (!studentRegistered) {
        showError('Please register your student information first');
        return;
    }

    try {
        // Check if browser supports getUserMedia
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Your browser does not support voice recording. Please try Chrome, Firefox, or Edge.');
        }

        // Request microphone access with detailed constraints
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 44100
            } 
        });

        // Try to use WAV format first, fallback to supported formats
        let mimeType = 'audio/wav';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
            if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                mimeType = 'audio/webm;codecs=opus';
            } else if (MediaRecorder.isTypeSupported('audio/webm')) {
                mimeType = 'audio/webm';
            } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
                mimeType = 'audio/mp4';
            } else {
                mimeType = ''; // Let browser choose
            }
        }

        mediaRecorder = new MediaRecorder(stream, {
            mimeType: mimeType
        });
        
        console.log('Using MIME type:', mediaRecorder.mimeType);
        
        audioChunks = [];

        mediaRecorder.ondataavailable = function(event) {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = function() {
            const audioBlob = new Blob(audioChunks, { 
                type: mediaRecorder.mimeType || 'audio/wav' 
            });
            const reader = new FileReader();
            reader.onload = function() {
                submitVoiceQuery(reader.result);
            };
            reader.readAsDataURL(audioBlob);
        };

        mediaRecorder.start();
        isRecording = true;

        // Update UI
        document.getElementById('recordBtn').disabled = true;
        document.getElementById('recordBtn').classList.add('recording');
        document.getElementById('stopBtn').disabled = false;
        document.getElementById('voiceStatus').innerHTML = '🔴 Recording... Click stop when finished';

        console.log('Recording started successfully');

    } catch (error) {
        console.error('Recording error:', error);
        
        let errorMessage = 'Unable to access microphone. ';
        
        if (error.name === 'NotAllowedError') {
            errorMessage += 'Please allow microphone access in your browser settings and refresh the page.';
        } else if (error.name === 'NotFoundError') {
            errorMessage += 'No microphone found. Please connect a microphone and try again.';
        } else if (error.name === 'NotSupportedError') {
            errorMessage += 'Your browser does not support voice recording. Please try Chrome, Firefox, or Edge.';
        } else if (error.name === 'SecurityError') {
            errorMessage += 'Microphone access blocked due to security restrictions. Please use HTTPS or localhost.';
        } else {
            errorMessage += error.message || 'Please check your microphone settings.';
        }
        
        showError(errorMessage);
        
        // Show detailed troubleshooting
        addMessage(`
🎤 **Microphone Troubleshooting:**

1. **Allow Permissions:** Click the 🔒 or 🛡️ icon in your address bar and allow microphone access
2. **Use Supported Browser:** Chrome, Firefox, Edge, or Safari
3. **Check URL:** Make sure you're using http://localhost:5000
4. **Test Microphone:** Ensure your microphone works in other applications
5. **Refresh Page:** After changing permissions, refresh the page

**Current URL:** ${window.location.href}
**Browser:** ${navigator.userAgent.includes('Chrome') ? 'Chrome' : navigator.userAgent.includes('Firefox') ? 'Firefox' : navigator.userAgent.includes('Safari') ? 'Safari' : 'Other'}
        `, 'ai');
    }
}

// Stop voice recording
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;

        // Update UI
        document.getElementById('recordBtn').disabled = false;
        document.getElementById('recordBtn').classList.remove('recording');
        document.getElementById('stopBtn').disabled = true;
        document.getElementById('voiceStatus').textContent = 'Processing audio...';
    }
}

// Submit voice query
async function submitVoiceQuery(audioData) {
    // Add user message
    addMessage('🎤 Voice message recorded', 'user');
    
    // Show loading
    showLoading(true);

    try {
        const response = await fetch('/api/query/voice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                audio_data: audioData
            })
        });

        const result = await response.json();

        if (result.success) {
            if (result.transcribed_text) {
                addMessage(`You said: "${result.transcribed_text}"`, 'transcribed-text');
            }
            addMessage(result.response, 'ai');
        } else {
            showError(result.error || 'Failed to process voice message');
        }
    } catch (error) {
        showError('Network error. Please check your connection.');
        console.error('Voice query error:', error);
    } finally {
        showLoading(false);
        document.getElementById('voiceStatus').textContent = '';
    }
}

// Drag and drop handlers
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        const fileInput = document.getElementById('imageFile');
        fileInput.files = files;
        handleImageUpload(fileInput);
    }
}

// Add message to response area
function addMessage(content, type) {
    const responseArea = document.getElementById('responseArea');
    
    // Clear welcome message if present
    if (responseArea.children.length === 1 && responseArea.children[0].style.textAlign === 'center') {
        responseArea.innerHTML = '';
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `response-message ${type}`;
    
    // Add appropriate icons and styling based on type
    let icon = '';
    switch (type) {
        case 'user':
            icon = '<i class="fas fa-user"></i> ';
            break;
        case 'ai':
            icon = '<i class="fas fa-robot"></i> ';
            break;
        case 'extracted-text':
            icon = '<i class="fas fa-eye"></i> ';
            break;
        case 'transcribed-text':
            icon = '<i class="fas fa-microphone"></i> ';
            break;
    }
    
    //messageDiv.innerHTML = `${icon}${content}`;
    messageDiv.innerHTML = `${icon}${formatText(content)}`;
    responseArea.appendChild(messageDiv);
    
    // Scroll to bottom
    responseArea.scrollTop = responseArea.scrollHeight;
}

// Show loading state
function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.add('show');
    } else {
        loading.classList.remove('show');
    }
}

// Show error message
function showError(message) {
    const responseArea = document.getElementById('responseArea');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
    responseArea.appendChild(errorDiv);
    responseArea.scrollTop = responseArea.scrollHeight;
}

// Show success message
function showSuccess(message) {
    const responseArea = document.getElementById('responseArea');
    const successDiv = document.createElement('div');
    successDiv.className = 'response-message';
    successDiv.style.background = '#c6f6d5';
    successDiv.style.borderLeftColor = '#48bb78';
    successDiv.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
    responseArea.appendChild(successDiv);
    responseArea.scrollTop = responseArea.scrollHeight;
}

function formatText(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')   // bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>')               // italic
        .replace(/\n/g, '<ul><li>')                         // line breaks
        .replace(/•/g, '🔹')                                // bullet emoji for bullets
        .replace(/^- /gm, '🔹 ');                           // or dashes used as bullets
}
