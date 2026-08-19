// =====================================================
// HAND WARS - ULTIMATE STONE PAPER SCISSORS ENGINE
// =====================================================

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initAudio();
    initWebcamHandlers();
    initConfettiIfWinner();
});

// =====================================================
// 1. THEME SWITCHER SYSTEM (LIGHT & DARK MODE)
// =====================================================

function initTheme() {
    const savedTheme = localStorage.getItem('handwars_theme') || 'dark';
    setTheme(savedTheme);

    const themeToggles = document.querySelectorAll('.theme-toggle-btn');
    themeToggles.forEach(btn => {
        btn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
            playSound('click');
        });
    });
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('handwars_theme', theme);

    const themeIcons = document.querySelectorAll('.theme-icon');
    const themeTexts = document.querySelectorAll('.theme-text');

    themeIcons.forEach(icon => {
        icon.textContent = theme === 'dark' ? '☀️' : '🌙';
    });
    themeTexts.forEach(text => {
        text.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
    });
}

// =====================================================
// 2. AUDIO SYNTHESIS
// =====================================================

let audioCtx = null;
let soundEnabled = localStorage.getItem('handwars_sound') !== 'false';

function initAudio() {
    const audioBtn = document.querySelectorAll('.sound-toggle-btn');
    updateSoundUI();

    audioBtn.forEach(btn => {
        btn.addEventListener('click', () => {
            soundEnabled = !soundEnabled;
            localStorage.setItem('handwars_sound', soundEnabled);
            updateSoundUI();
            if (soundEnabled) playSound('click');
        });
    });
}

function updateSoundUI() {
    const soundIcons = document.querySelectorAll('.sound-icon');
    soundIcons.forEach(icon => {
        icon.textContent = soundEnabled ? '🔊' : '🔇';
    });
}

function playSound(type) {
    if (!soundEnabled) return;

    try {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }

        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);

        const now = audioCtx.currentTime;

        if (type === 'click') {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(440, now);
            osc.frequency.exponentialRampToValueAtTime(880, now + 0.08);
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
            osc.start(now);
            osc.stop(now + 0.08);
        } else if (type === 'snap') {
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(600, now);
            osc.frequency.exponentialRampToValueAtTime(200, now + 0.15);
            gain.gain.setValueAtTime(0.25, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
            osc.start(now);
            osc.stop(now + 0.15);
        } else if (type === 'win') {
            const notes = [523.25, 659.25, 783.99, 1046.50];
            notes.forEach((freq, idx) => {
                const noteOsc = audioCtx.createOscillator();
                const noteGain = audioCtx.createGain();
                noteOsc.type = 'sine';
                noteOsc.frequency.value = freq;
                noteOsc.connect(noteGain);
                noteGain.connect(audioCtx.destination);

                const startTime = now + (idx * 0.1);
                noteGain.gain.setValueAtTime(0.2, startTime);
                noteGain.gain.exponentialRampToValueAtTime(0.01, startTime + 0.25);

                noteOsc.start(startTime);
                noteOsc.stop(startTime + 0.25);
            });
        }
    } catch (e) {
        console.warn("Audio error:", e);
    }
}

// =====================================================
// 3. WEBCAM & INPUT TAB SYSTEM
// =====================================================

let activeStreams = {};

function initWebcamHandlers() {
    const tabBtns = document.querySelectorAll('.input-tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetId = btn.getAttribute('data-target');
            const parentCard = btn.closest('.player-card');

            parentCard.querySelectorAll('.input-tab-btn').forEach(b => b.classList.remove('active'));
            parentCard.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            parentCard.querySelector(`#${targetId}`).classList.add('active');
            playSound('click');

            if (targetId.includes('webcam')) {
                const pId = targetId.startsWith('p1') ? 'p1' : 'p2';
                startWebcam(pId);
            }
        });
    });

    if (document.getElementById('webcam-p1')) startWebcam('p1');
    if (document.getElementById('webcam-p2')) startWebcam('p2');
}

async function startWebcam(playerKey) {
    const video = document.getElementById(`webcam-${playerKey}`);
    const statusMsg = document.getElementById(`${playerKey}-status`);

    if (!video) return;

    try {
        if (activeStreams[playerKey]) return;

        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" }
        });
        video.srcObject = stream;
        activeStreams[playerKey] = stream;
        if (statusMsg) statusMsg.textContent = "Camera active! Align hand gesture inside frame & capture.";
    } catch (err) {
        console.error("Camera access error:", err);
        if (statusMsg) statusMsg.textContent = "⚠️ Webcam unavailable. Use 'Manual Choice' tab to pick your move!";
    }
}

function captureAndSubmit(playerKey, actionUrl) {
    playSound('snap');
    const video = document.getElementById(`webcam-${playerKey}`);
    const canvas = document.getElementById(`canvas-${playerKey}`);
    const form = document.getElementById(`form-${playerKey}`);

    if (video && video.srcObject && canvas) {
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        const ctx = canvas.getContext('2d');

        // Mirror canvas drawing to match on-screen selfie camera preview
        ctx.save();
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        ctx.restore();

        canvas.toBlob((blob) => {
            const file = new File([blob], "webcam_move.jpg", { type: "image/jpeg" });
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            const fileInput = document.getElementById(`file-${playerKey}`);
            if (fileInput) {
                fileInput.files = dataTransfer.files;
            }
            form.submit();
        }, "image/jpeg", 0.95);
    } else {
        const fileInput = document.getElementById(`file-${playerKey}`);
        if (fileInput) fileInput.click();
    }
}

function submitManualMove(playerKey, moveValue, actionUrl) {
    playSound('click');
    const form = document.getElementById(`form-${playerKey}`);
    let manualInput = form.querySelector('input[name="manual_move"]');
    if (!manualInput) {
        manualInput = document.createElement('input');
        manualInput.type = 'hidden';
        manualInput.name = 'manual_move';
        form.appendChild(manualInput);
    }
    manualInput.value = moveValue;
    form.submit();
}

// =====================================================
// 4. CONFETTI CELEBRATION
// =====================================================

function initConfettiIfWinner() {
    const isResultPage = document.querySelector('.result-panel') || document.querySelector('.round-result-card');
    const isFinalPage = document.querySelector('.final-card');

    if (isResultPage || isFinalPage) {
        playSound('win');
        createConfetti();
    }
}

function createConfetti() {
    const colors = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899'];
    const container = document.body;

    for (let i = 0; i < 40; i++) {
        const piece = document.createElement('div');
        piece.className = 'confetti-piece';
        piece.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        piece.style.left = Math.random() * 100 + 'vw';
        piece.style.animationDuration = (Math.random() * 2 + 2) + 's';
        piece.style.animationDelay = (Math.random() * 0.5) + 's';
        container.appendChild(piece);

        setTimeout(() => piece.remove(), 4500);
    }
}
