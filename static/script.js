// Test comment
let previousWeather = "";
let previousNews = "";
let previousCrypto = "";
let previousCalendar = "";
const socket = io();
let currentTryOnItems = [];
let liveTryOn = null; // To hold our live try-on instance
let currentAudio = null;
const audioQueue = [];
let isAudioPlaying = false;


// Socket.IO listeners
socket.on('connect', () => {
    console.log('🔌 Socket.IO connected!');
});

socket.on('play_audio', (data) => {
    console.log('▶️ Received play_audio event', data);
    audioQueue.push(data);
    if (!isAudioPlaying) {
        processAudioQueue();
    }
});

socket.on('stop_audio', () => {
    console.log('⏹️ Received stop_audio event');
    audioQueue.length = 0; // Clear the queue

    if (currentAudio) {
        currentAudio.pause();
        currentAudio.src = ''; // Release resources
    }

    isAudioPlaying = false; // Reset playing state
    const voiceBox = document.getElementById('voice-response');
    voiceBox.classList.remove('speaking');
    voiceBox.classList.remove('listening');

    const micIcon = document.getElementById('mic-icon');
    if(micIcon) micIcon.classList.remove('listening');

    document.getElementById("voice-text").textContent = "";
});

socket.on('start_listening', () => {
    console.log('🎤 Started listening');
    const voiceBox = document.getElementById('voice-response');
    voiceBox.classList.add('listening');

    const micIcon = document.getElementById('mic-icon');
    if(micIcon) micIcon.classList.add('listening');

    document.getElementById('voice-text').textContent = 'Listening...';
});

socket.on('stop_listening', () => {
    console.log('🛑 Stopped listening');
    const voiceBox = document.getElementById('voice-response');
    voiceBox.classList.remove('listening');

    const micIcon = document.getElementById('mic-icon');
    if(micIcon) micIcon.classList.remove('listening');

    document.getElementById('voice-text').textContent = '';
});

socket.on("hide_tryon", () => {
    console.log("Hiding try-on interface.");
    toggleWidgetsVisibility(false, false); // Show main widgets, hide all try-on

    if (liveTryOn) {
        liveTryOn.stop();
        liveTryOn = null;
    }
});

socket.on("trigger_tryon", (data) => {
    console.log("Try-on trigger received:", data);

    if (!data.category) {
        toggleWidgetsVisibility(false, false);
        document.getElementById("product-options").innerHTML = `
            <span style="color:white;">No matching items found.</span>
        `;
        setTimeout(() => {
            document.getElementById("product-options").innerHTML = "";
        }, 4000);
        return;
    }

    showTryOnOptions(data.category, data.color, data.max_price);
});

socket.on("try_on_selected_item", ({ index }) => {
    console.log("Selected item index:", index);

    const item = currentTryOnItems[index];
    if (item) {
        toggleWidgetsVisibility(false, true); // Hide options, show preview
        if (liveTryOn) {
            liveTryOn.setOverlay(item.processed_image_url);
        } else {
            console.error("Live Try-On not initialized, but it should be.");
        }
    } else {
        console.error("Selected item index out of bounds:", index);
    }
});


// Update Time and Date
function updateTimeAndDate() {
    fetch('/time_date')
        .then(response => response.json())
        .then(data => {
            let timeElement = document.getElementById('time');
            let dateElement = document.getElementById('date');

            // Check if content is actually changing
            if (timeElement.textContent !== data.time) {
                timeElement.textContent = data.time;
                timeElement.classList.add('widget-update');
                setTimeout(() => timeElement.classList.remove('widget-update'), 300);
            }

            if (dateElement.textContent !== data.date) {
                dateElement.textContent = data.date;
                dateElement.classList.add('widget-update');
                setTimeout(() => dateElement.classList.remove('widget-update'), 300);
            }
        });
}

// Update Weather
function updateWeather() {
    fetch('/weather')
        .then(response => response.json())
        .then(data => {
            let newWeatherText = `${data.weather[0].description}, ${data.main.temp}°C`;
            let weatherDesc = document.getElementById('weather-description');
            let weatherIcon = document.getElementById('weather-icon');

            if (previousWeather !== newWeatherText) { // Only update if data changes
                previousWeather = newWeatherText;
                weatherDesc.textContent = newWeatherText;
                weatherDesc.classList.add('widget-update');
                setTimeout(() => weatherDesc.classList.remove('widget-update'), 300);
            }

            weatherIcon.src = data.weather[0].icon;
        })
        .catch(error => console.error('Error fetching weather:', error));
}


// Update News
function updateNews() {
    fetch('/news')
        .then(response => response.json())
        .then(data => {
            let newsElement = document.getElementById('news-content');
            let latestNews = `News: ${data.articles[0].title}`;

            if (previousNews !== latestNews) {
                previousNews = latestNews;
                newsElement.textContent = latestNews;
                newsElement.classList.add('widget-update');
                setTimeout(() => newsElement.classList.remove('widget-update'), 300);
            }
        });
}

// Update Crypto Prices
function updateCrypto() {
    fetch('/crypto')
        .then(response => response.json())
        .then(data => {
            let cryptoElement = document.getElementById('crypto-content');
            let newCryptoText = `Bitcoin: $${data.bitcoin}, Ethereum: $${data.ethereum}`;

            if (previousCrypto !== newCryptoText) {
                previousCrypto = newCryptoText;
                cryptoElement.textContent = newCryptoText;
                cryptoElement.classList.add('widget-update');
                setTimeout(() => cryptoElement.classList.remove('widget-update'), 300);
            }
        });
}

// Update Calendar
function updateCalendar() {
    fetch('/calendar')
        .then(response => response.json())
        .then(data => {
            let calendarDiv = document.getElementById('calendar-content');

            if (data.error) {
                calendarDiv.textContent = "Failed to load calendar events.";
            } else if (data.message) {
                calendarDiv.textContent = data.message;
            } else if (data.length === 0) {
                calendarDiv.textContent = "No upcoming events.";
            } else {
                let newCalendarHTML = data.map(event => {
                    const eventDate = new Date(event.start.dateTime || event.start.date);
                    const now = new Date();

                    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                    const tomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
                    const eventDay = new Date(eventDate.getFullYear(), eventDate.getMonth(), eventDate.getDate());

                    let dayString = '';
                    if (eventDay.getTime() === today.getTime()) {
                        dayString = 'today';
                    } else if (eventDay.getTime() === tomorrow.getTime()) {
                        dayString = 'tomorrow';
                    } else {
                        // Fallback for other days, maybe show date
                        dayString = eventDate.toLocaleDateString(undefined, {
                            weekday: 'long'
                        });
                    }

                    const timeString = eventDate.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: false
                    });

                    return `<div class="calendar-event">${event.summary} - ${timeString} ${dayString}</div>`;
                }).join('');

                if (previousCalendar !== newCalendarHTML) {
                    previousCalendar = newCalendarHTML;
                    calendarDiv.innerHTML = newCalendarHTML;
                    calendarDiv.classList.add('widget-update');
                    setTimeout(() => calendarDiv.classList.remove('widget-update'), 300);
                }
            }
        })
        .catch(error => {
            console.error("Error fetching calendar:", error);
            document.getElementById('calendar').textContent = "Error loading calendar.";
        });
}

// Function to update background theme based on time
function updateTheme() {
    const hour = new Date().getHours();
    const body = document.body;
    const themes = ['theme-morning', 'theme-afternoon', 'theme-evening', 'theme-night'];

    // Remove any existing theme classes
    body.classList.remove(...themes);

    if (hour >= 5 && hour < 11) {
        body.classList.add('theme-morning');
    } else if (hour >= 11 && hour < 17) {
        body.classList.add('theme-afternoon');
    } else if (hour >= 17 && hour < 21) {
        body.classList.add('theme-evening');
    } else {
        body.classList.add('theme-night');
    }
}


function processAudioQueue() {
    if (audioQueue.length === 0 || isAudioPlaying) {
        return;
    }

    isAudioPlaying = true;
    const data = audioQueue.shift();
    playSpeechAudio(data.audio_url, data.text);
}


function playSpeechAudio(audioUrl, text) {
    const voiceText = document.getElementById('voice-text');
    voiceText.textContent = text;

    const canvas = document.getElementById('voice-visualizer');
    const ctx = canvas.getContext('2d');
    const voiceBox = document.getElementById('voice-response');

    if (!audioUrl) {
        console.warn("⚠ No audio URL provided. Skipping voice playback.");
        isAudioPlaying = false;
        processAudioQueue();
        return;
    }

    const audio = new Audio(audioUrl);
    currentAudio = audio; // Assign to global variable

    const audioContext = new(window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaElementSource(audio);
    const analyser = audioContext.createAnalyser();
    const gainNode = audioContext.createGain();

    source.connect(analyser);
    analyser.connect(gainNode);
    gainNode.connect(audioContext.destination);

    analyser.fftSize = 2048;
    const bufferLength = analyser.fftSize;
    const dataArray = new Uint8Array(bufferLength);

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    if (canvas.width === 0 || canvas.height === 0) {
        canvas.width = 360;
        canvas.height = 40;
    }

    voiceBox.classList.add('speaking');

    let animationFrameId;

    audio.onended = () => {
        console.log('Audio finished playing.');
        socket.emit('audio_finished');
        isAudioPlaying = false;
        processAudioQueue();
    };

    function drawSineWave() {
        analyser.getByteTimeDomainData(dataArray);

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.lineWidth = 2;
        ctx.strokeStyle = 'rgba(0, 200, 255, 0.8)';
        ctx.beginPath();

        const sliceWidth = canvas.width / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0;
            const y = (v * canvas.height) / 2;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }

            x += sliceWidth;
        }

        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();

        if (!audio.paused && !audio.ended) {
            animationFrameId = requestAnimationFrame(drawSineWave);
        } else {
            voiceBox.classList.remove('speaking');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            cancelAnimationFrame(animationFrameId);
        }
    }

    audio.play()
        .then(() => {
            console.log("Audio started successfully.");
            drawSineWave();
        })
        .catch(error => {
            console.error("Audio playback failed:", error);
            isAudioPlaying = false;
            processAudioQueue(); // Try next in queue
        });
}

document.addEventListener('DOMContentLoaded', () => {
    const initButton = document.getElementById('audio-init-button');
    if (initButton) {
        initButton.addEventListener('click', () => {
            console.log("Audio context initialized by user gesture.");
            triggerVoicePlayback();
            initButton.classList.add('hidden');
        });
    }

    // Initial data fetch
    updateTimeAndDate();
    updateWeather();
    updateNews();
    updateCrypto();
    updateCalendar();
    updateTheme(); // Set initial theme

    // Set intervals for updates
    setInterval(updateTimeAndDate, 60000); // Every minute
    setInterval(updateWeather, 600000); // Every 10 minutes
    setInterval(updateNews, 900000); // Every 15 minutes
    setInterval(updateCrypto, 300000); // Every 5 minutes
    setInterval(updateCalendar, 900000); // Every 15 minutes
    setInterval(updateTheme, 60000); // Update theme every minute
});


function triggerVoicePlayback(retries = 5, delay = 500) {
    const voiceText = document.getElementById('voice-text');

    function tryFetchAudio(attempt = 1) {
        fetch('/voice_command')
            .then(response => response.json())
            .then(data => {
                if (data.response_audio) {
                    console.log("Found audio:", data.response_audio);
                    audioQueue.push({
                        audio_url: data.response_audio,
                        text: data.text
                    });
                    if (!isAudioPlaying) {
                        processAudioQueue();
                    }
                } else {
                    if (attempt < retries) {
                        console.warn(`⏳ Audio not ready yet (attempt ${attempt}). Retrying in ${delay}ms...`);
                        setTimeout(() => tryFetchAudio(attempt + 1), delay);
                    } else {
                        console.error("Audio file was never found after retries.");
                        voiceText.textContent = "Voice assistant is running in the background.";
                    }
                }
            })
            .catch(error => {
                console.error("Error fetching voice response:", error);
                voiceText.textContent = "Voice error.";
            });
    }

    tryFetchAudio();
}

function showTryOnOptions(category = "men's clothing", color = null, max_price = null) {
    const url = new URL("/find_clothing", window.location.origin);
    if (category) url.searchParams.append("category", category);
    if (color) url.searchParams.append("color", color);
    if (max_price) url.searchParams.append("max_price", max_price);

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.error || data.message) {
                console.warn("No matching items or user not logged in:", data);
                return;
            }

            currentTryOnItems = data;

            const container = document.getElementById("product-options");
            container.innerHTML = "";

            data.forEach((item, index) => {
                const card = document.createElement("div");
                card.className = "product-card";
                card.innerHTML = `
                    <img src="${item.image_url}" alt="product-${index}" />
                    <span><strong>Option ${index + 1}</strong></span>
                    <span>${item.title}</span>
                    <span>${item.price} lei</span>
                `;
                container.appendChild(card);
            });

            toggleWidgetsVisibility(true, false); // Show options, hide preview

            setTimeout(() => {
                const tryOnOptions = document.getElementById('tryon-options');
                if (tryOnOptions.style.display === 'block') {
                    toggleWidgetsVisibility(false, false);
                    console.log("Auto-hide triggered: try-on options removed after 30s.");
                }
            }, 30000); // 30 seconds

        })
        .catch(error => console.error("Error loading try-on options:", error));
}


function toggleWidgetsVisibility(showOptions, showPreview) {
    const widgetsToToggle = ['weather', 'news', 'crypto', 'calendar'];
    const shouldHideWidgets = showOptions || showPreview;

    widgetsToToggle.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.style.display = shouldHideWidgets ? 'none' : 'flex';
        }
    });

    const tryOnWidget = document.getElementById('tryon-options');
    if (tryOnWidget) {
        tryOnWidget.style.display = showOptions ? 'block' : 'none';
    }

    const tryOnPreview = document.getElementById('tryon-preview');
    if (tryOnPreview) {
        tryOnPreview.style.display = showPreview ? 'block' : 'none';
        if (showPreview && !liveTryOn) {
            liveTryOn = new LiveTryOn();
        } else if (!showPreview && liveTryOn) {
            liveTryOn.stop();
            liveTryOn = null;
        }
    }
}


class LiveTryOn {
    constructor() {
        this.videoElement = document.getElementById('input_video');
        this.canvasElement = document.getElementById('output_canvas');
        this.canvasCtx = this.canvasElement.getContext('2d');
        this.overlayImage = new Image();
        this.pose = new Pose({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`,
        });

        this.pose.setOptions({
            modelComplexity: 1,
            smoothLandmarks: true,
            enableSegmentation: false,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        this.pose.onResults(this.onPoseResults.bind(this));

        this.camera = new Camera(this.videoElement, {
            onFrame: async () => {
                await this.pose.send({
                    image: this.videoElement
                });
            },
            width: 640,
            height: 480
        });
        this.camera.start();
        this.startCloseTimer();
        console.log("Live Try-On session started.");
    }

    startCloseTimer() {
        this.closeTimer = setTimeout(() => {
            console.log("Auto-closing try-on session after 20 seconds of inactivity.");
            this.stop();
            toggleWidgetsVisibility(false, false); // Return to default view
        }, 20000); // 20 seconds
    }

    setOverlay(imageUrl) {
        if(imageUrl) {
            this.overlayImage.src = imageUrl;
        } else {
            console.warn("No overlay image URL provided.");
        }
    }

    onPoseResults(results) {
        if (!results.poseLandmarks) {
            return;
        }
        this.canvasCtx.save();
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
        this.canvasCtx.drawImage(results.image, 0, 0, this.canvasElement.width, this.canvasElement.height);
        
        if (this.overlayImage.src) {
           this.drawOverlay(results.poseLandmarks);
        }

        this.canvasCtx.restore();
    }
    
    drawOverlay(landmarks) {
        const leftShoulder = landmarks[11];
        const rightShoulder = landmarks[12];
        const leftHip = landmarks[23];
        const rightHip = landmarks[24];
    
        if (leftShoulder && rightShoulder && leftHip && rightHip) {
            const shoulderWidth = Math.abs(rightShoulder.x - leftShoulder.x) * this.canvasElement.width;
            const bodyHeight = Math.abs(leftHip.y - leftShoulder.y) * this.canvasElement.height;
    
            const centerX = (leftShoulder.x + rightShoulder.x) / 2 * this.canvasElement.width;
            const centerY = (leftShoulder.y + rightShoulder.y) / 2 * this.canvasElement.height;
    
            const scaleRatio = 2.5; 
            const scaledWidth = shoulderWidth * scaleRatio;
            const aspectRatio = this.overlayImage.naturalHeight / this.overlayImage.naturalWidth;
            const scaledHeight = scaledWidth * aspectRatio;
    
            const drawX = centerX - scaledWidth / 2;
            const drawY = centerY - (scaledHeight * 0.1); 
    
            this.canvasCtx.drawImage(this.overlayImage, drawX, drawY, scaledWidth, scaledHeight);
        }
    }
    

    stop() {
        this.camera.stop();
        this.pose.close();
        clearTimeout(this.closeTimer);
        console.log("Live Try-On session stopped.");
    }
}
