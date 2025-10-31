// Global persistent audio player that works across all pages
class GlobalAudioPlayer {
    constructor() {
        this.audio = null;
        this.audioContext = null;
        this.analyser = null;
        this.audioSource = null;
        this.animationId = null;
        this.storageKey = 'dotm_audio_state';
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initAudioPlayer());
        } else {
            this.initAudioPlayer();
        }
    }

    initAudioPlayer() {
        // Create audio element if it doesn't exist
        if (!document.getElementById('globalAudioPlayer')) {
            this.audio = document.createElement('audio');
            this.audio.id = 'globalAudioPlayer';
            this.audio.preload = 'metadata';
            document.body.appendChild(this.audio);
        } else {
            this.audio = document.getElementById('globalAudioPlayer');
        }

        // Create mini player UI
        this.createMiniPlayer();

        // Set up event listeners
        this.setupEventListeners();

        // Restore state if exists
        this.restoreState();
        
        console.log('Global audio player fully initialized with mini player');
    }

    createMiniPlayer() {
        // Check if mini player already exists
        if (document.getElementById('globalMiniPlayer')) {
            console.log('Mini player already exists');
            return;
        }

        const miniPlayer = document.createElement('div');
        miniPlayer.id = 'globalMiniPlayer';
        miniPlayer.className = 'global-mini-player';
        miniPlayer.style.display = 'none';
        
        miniPlayer.innerHTML = `
            <div class="mini-player-content">
                <div class="mini-player-info">
                    <div class="mini-player-title">Welcome Message</div>
                    <div class="mini-player-details">
                        <span id="miniPlayerLanguage">EN</span> • 
                        <span id="miniPlayerVoice">ScienceTeacher</span>
                    </div>
                </div>
                <div class="mini-player-controls">
                    <button id="miniPlayerPlayPause" class="mini-player-btn">
                        <i class="fas fa-pause"></i>
                    </button>
                    <button id="miniPlayerClose" class="mini-player-btn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <canvas id="miniPlayerVisualizer" width="200" height="40"></canvas>
            </div>
        `;
        
        document.body.appendChild(miniPlayer);
        console.log('Mini player created and added to DOM');

        // Set up mini player controls
        document.getElementById('miniPlayerPlayPause').addEventListener('click', () => {
            this.togglePlayPause();
        });

        document.getElementById('miniPlayerClose').addEventListener('click', () => {
            this.stop();
        });
    }

    setupEventListeners() {
        this.audio.addEventListener('play', () => {
            this.showMiniPlayer();
            this.updatePlayPauseButton(true);
            this.saveState();
            this.startVisualization();
        });

        this.audio.addEventListener('pause', () => {
            this.updatePlayPauseButton(false);
            this.saveState();
            this.stopVisualization();
        });

        this.audio.addEventListener('ended', () => {
            this.onAudioEnded();
        });

        this.audio.addEventListener('timeupdate', () => {
            this.saveState();
        });

        // Handle page unload - save state
        window.addEventListener('beforeunload', () => {
            this.saveState();
        });

        // Handle page load - restore state
        window.addEventListener('load', () => {
            this.restoreState();
        });
    }

    play(audioUrl, metadata = {}) {
        // Get the current playback position before changing source
        const previousPosition = this.audio.currentTime || 0;
        const wasPaused = this.audio.paused;
        
        this.audio.src = audioUrl;
        
        // Save metadata
        const state = this.getState() || {};
        state.metadata = metadata;
        sessionStorage.setItem(this.storageKey, JSON.stringify(state));

        // Update mini player info
        if (metadata.language) {
            document.getElementById('miniPlayerLanguage').textContent = metadata.language.toUpperCase();
        }
        if (metadata.voiceProfile) {
            document.getElementById('miniPlayerVoice').textContent = metadata.voiceProfile;
        }

        // Set the playback position to 5 seconds before the previous position
        this.audio.addEventListener('loadedmetadata', () => {
            const resumePosition = Math.max(0, previousPosition - 5);
            this.audio.currentTime = resumePosition;
            console.log(`Resuming audio from ${resumePosition.toFixed(1)}s (previous: ${previousPosition.toFixed(1)}s)`);
        }, { once: true });

        this.audio.play().catch(error => {
            console.error('Error playing audio:', error);
        });
    }

    togglePlayPause() {
        if (this.audio.paused) {
            this.audio.play();
        } else {
            this.audio.pause();
        }
    }

    stop() {
        this.audio.pause();
        this.audio.currentTime = 0;
        this.hideMiniPlayer();
        this.clearState();
        this.stopVisualization();
        
        // Also hide the dashboard visualizer if it exists
        const dashboardVisualizer = document.getElementById('audioVisualizer');
        if (dashboardVisualizer) {
            dashboardVisualizer.style.display = 'none';
        }
    }

    showMiniPlayer() {
        const miniPlayer = document.getElementById('globalMiniPlayer');
        if (miniPlayer) {
            miniPlayer.style.display = 'flex';
            console.log('Mini player shown');
        } else {
            console.error('Mini player element not found! Creating it now...');
            this.createMiniPlayer();
            const newMiniPlayer = document.getElementById('globalMiniPlayer');
            if (newMiniPlayer) {
                newMiniPlayer.style.display = 'flex';
            }
        }
    }

    hideMiniPlayer() {
        const miniPlayer = document.getElementById('globalMiniPlayer');
        if (miniPlayer) {
            miniPlayer.style.display = 'none';
        }
    }

    updatePlayPauseButton(isPlaying) {
        const btn = document.getElementById('miniPlayerPlayPause');
        if (btn) {
            btn.innerHTML = isPlaying ? '<i class="fas fa-pause"></i>' : '<i class="fas fa-play"></i>';
        }
    }

    saveState() {
        const state = {
            src: this.audio.src,
            currentTime: this.audio.currentTime,
            paused: this.audio.paused,
            metadata: (this.getState() || {}).metadata || {}
        };
        sessionStorage.setItem(this.storageKey, JSON.stringify(state));
    }

    getState() {
        const stateStr = sessionStorage.getItem(this.storageKey);
        return stateStr ? JSON.parse(stateStr) : null;
    }

    restoreState() {
        const state = this.getState();
        if (state && state.src) {
            this.audio.src = state.src;
            this.audio.currentTime = state.currentTime || 0;

            // Restore metadata to mini player
            if (state.metadata) {
                if (state.metadata.language) {
                    document.getElementById('miniPlayerLanguage').textContent = state.metadata.language.toUpperCase();
                }
                if (state.metadata.voiceProfile) {
                    document.getElementById('miniPlayerVoice').textContent = state.metadata.voiceProfile;
                }
            }

            if (!state.paused) {
                this.audio.play().catch(error => {
                    console.log('Auto-play prevented, user interaction required');
                    this.showMiniPlayer();
                });
            } else {
                this.showMiniPlayer();
            }
        }
    }

    clearState() {
        sessionStorage.removeItem(this.storageKey);
    }

    onAudioEnded() {
        this.hideMiniPlayer();
        this.clearState();
        this.stopVisualization();

        // Track that the message was listened to completion
        const state = this.getState();
        if (state && state.metadata) {
            this.trackListenCompletion(state.metadata);
        }

        // Trigger any dashboard-specific completion handlers
        if (window.onGlobalAudioEnded) {
            window.onGlobalAudioEnded();
        }
    }

    trackListenCompletion(metadata) {
        if (metadata.firebaseUid && metadata.messageType) {
            fetch('/api/welcome-message/track-listen', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    firebase_uid: metadata.firebaseUid,
                    message_type: metadata.messageType,
                    completed: true
                })
            }).catch(error => {
                console.error('Error tracking message listen:', error);
            });
        }
    }

    startVisualization() {
        const canvas = document.getElementById('miniPlayerVisualizer');
        if (!canvas) return;

        // Initialize audio context if needed
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
        }

        // Connect audio source if not already connected
        if (!this.audioSource) {
            this.audioSource = this.audioContext.createMediaElementSource(this.audio);
            this.audioSource.connect(this.analyser);
            this.analyser.connect(this.audioContext.destination);
        }

        const canvasCtx = canvas.getContext('2d');
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        // Set canvas size to match parent container dimensions
        const parentWidth = canvas.parentElement.offsetWidth;
        const parentHeight = canvas.parentElement.offsetHeight;
        canvas.width = parentWidth;
        canvas.height = parentHeight;

        const draw = () => {
            this.animationId = requestAnimationFrame(draw);
            this.analyser.getByteFrequencyData(dataArray);

            canvasCtx.fillStyle = 'rgba(102, 126, 234, 0.1)';
            canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

            const barWidth = (canvas.width / bufferLength) * 2.5;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const barHeight = (dataArray[i] / 255) * canvas.height;
                canvasCtx.fillStyle = `rgb(${dataArray[i] + 100}, 126, 234)`;
                canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                x += barWidth + 1;
            }
        };

        draw();
    }

    stopVisualization() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }

        // Clear the canvas
        const canvas = document.getElementById('miniPlayerVisualizer');
        if (canvas) {
            const canvasCtx = canvas.getContext('2d');
            canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }

    isPlaying() {
        return !this.audio.paused;
    }
}

// Create global instance
window.globalAudioPlayer = new GlobalAudioPlayer();

console.log('Global audio player initialized');
