let recognition;
let videoStream;

if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
}

function startListening() {
    if (!recognition) {
        alert("Speech recognition not supported in this browser.");
        return;
    }

    recognition.start();
    recognition.onresult = function(event) {
        const voiceText = event.results[0][0].transcript;
        document.getElementById("question").value = voiceText;
    };

    recognition.onerror = function(event) {
        console.error("Speech recognition error", event);
        alert("Voice input error: " + event.error);
    };
}

async function sendQuestion() {
    const question = document.getElementById("question").value;
    const classLevel = document.getElementById("class").value;
    const board = document.getElementById("board").value;
    const language = document.getElementById("language").value;

    if (!question.trim()) {
        alert("Please enter your question.");
        return;
    }

    const formData = new FormData();
    formData.append("question", question);
    formData.append("class_level", classLevel);
    formData.append("board", board);
    formData.append("language", language);

    try {
        const res = await fetch("http://localhost:8000/ask", {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        showResponse(data.response);
    } catch (err) {
        console.error("Error:", err);
        alert("Failed to fetch response.");
    }
}

function uploadImage() {
    const file = document.getElementById("imageInput").files[0];
    if (!file) {
        alert("Please select an image to upload.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    fetch("http://localhost:8000/upload-image", {
        method: "POST",
        body: formData
    }).then(res => res.json()).then(data => {
        if (data.extracted_text) {
            alert("📄 Extracted Text: " + data.extracted_text);
        }
        showResponse(data.response || "✅ Image processed.");
    }).catch(err => {
        console.error("Image upload failed:", err);
        alert("Failed to upload or process image.");
    });
}

function showResponse(text) {
    const responseEl = document.getElementById("response");
    responseEl.innerText = text;
    document.getElementById("responseSection").style.display = "block";
    readAnswer(text);
}

function readAnswer(text) {
    const cleanText = text
        .replace(/[*#=_~^{}[\]|<>]/g, "")
        .replace(/[\u231A-\uD83E\uDDFF]/g, "")
        .replace(/(:|;|=)[-~]?[)D]/g, "")
        .replace(/\\n+/g, ". ");

    const msg = new SpeechSynthesisUtterance(cleanText);
    const voices = window.speechSynthesis.getVoices();
    const preferredVoices = voices.filter(v =>
        v.name.includes("Google") && (v.lang === "en-IN" || v.lang === "hi-IN")
    );
    msg.voice = preferredVoices.length > 0 ? preferredVoices[0] : voices[0];
    msg.lang = msg.voice.lang;
    msg.rate = 0.95;
    msg.pitch = 1.0;
    msg.volume = 1;

    window.speechSynthesis.speak(msg);
}

window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices();
};

// ========== 📸 Camera ==========

function startCamera() {
    const video = document.getElementById("video");
    const preview = document.getElementById("previewImage");
    preview.style.display = "none";

    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            videoStream = stream;
            video.srcObject = stream;
            video.style.display = "block";
            document.getElementById("stopBtn").style.display = "inline-block";
        })
        .catch(err => {
            console.error("Camera access denied:", err);
            alert("Could not access camera.");
        });
}

function stopCamera() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    document.getElementById("video").style.display = "none";
    document.getElementById("stopBtn").style.display = "none";
}

function captureImage() {
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    const preview = document.getElementById("previewImage");
    preview.src = canvas.toDataURL("image/jpeg");
    preview.style.display = "block";

    canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append("file", blob, "capture.jpg");

        fetch("http://localhost:8000/upload-image", {
            method: "POST",
            body: formData
        }).then(res => res.json()).then(data => {
            if (data.extracted_text) {
                alert("📸 Extracted Text: " + data.extracted_text);
            }
            showResponse(data.response || "Captured image processed.");
            stopCamera();
        }).catch(err => {
            console.error("Capture upload failed:", err);
            alert("Failed to process captured image.");
        });
    }, "image/jpeg");
}
