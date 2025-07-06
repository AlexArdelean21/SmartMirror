let previousWeather = "";
let previousNews = "";
let previousCrypto = "";
let previousCalendar = "";
const socket = io();
let currentTryOnItems = [];
let liveTryOn = null; // To hold our live try-on instance

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

            if (previousWeather !== newWeatherText) {  // Only update if data changes
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

// Poll Voice Responses and Update UI
//function pollVoiceResponse() {
//    fetch('/voice_command')
//        .then(response => response.json())
//        .then(data => {
//            if (data.response_audio) {
//                playSpeechAudio(data.response_audio);
//                document.getElementById('voice-text').textContent = data.text;
//            }
//        })
//        .catch(error => console.error('Error fetching voice response:', error));
//}

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
                let newCalendarHTML = data.map(event =>
                    `<div class="calendar-event">${event.summary} - ${event.start.dateTime || event.start.date}</div>`
                ).join('');

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


function playSpeechAudio(audioUrl) {
    console.log("📢 [playSpeechAudio] Audio URL:", audioUrl);

    const canvas = document.getElementById('voice-visualizer');
    const ctx = canvas.getContext('2d');
    const voiceBox = document.getElementById('voice-response');

    if (!audioUrl) {
        console.warn("⚠ No audio URL provided. Skipping voice playback.");
        return;
    }

    const audio = new Audio(audioUrl);
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
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
        });
}

document.getElementById('audio-init-button').addEventListener('click', () => {
    const audio = new Audio();
    audio.play().catch(() => {
        console.warn("Silent boot play failed, continuing...");
    });

    document.getElementById('audio-init-button').classList.add('hidden');

    setTimeout(() => {
        triggerVoicePlayback();
    }, 2000);
});


function triggerVoicePlayback(retries = 5, delay = 500) {
    const voiceText = document.getElementById('voice-text');

    function tryFetchAudio(attempt = 1) {
        fetch('/voice_command')
            .then(response => response.json())
            .then(data => {
                if (data.response_audio) {
                    console.log("Found audio:", data.response_audio);
                    playSpeechAudio(data.response_audio);
                    voiceText.textContent = data.text;
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

socket.on("play_audio", (data) => {
    console.log("[Socket] Received voice playback:", data);
    playSpeechAudio(data.audio_url);
    document.getElementById("voice-text").textContent = data.text;
});

socket.on("start_listening", () => {
    document.getElementById("voice-text").textContent = "Listening...";
    document.getElementById("voice-response").classList.add("listening");
    document.getElementById("mic-icon").classList.add("listening");
});

socket.on("stop_listening", () => {
    document.getElementById("voice-text").textContent = "";
    document.getElementById("voice-response").classList.remove("listening");
    document.getElementById("mic-icon").classList.remove("listening");
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
            console.warn("No item found for selected index:", index);
        }
    });

    const { category, color, max_price } = data;
    showTryOnOptions(category, color, max_price);
});

class LiveTryOn {
    constructor() {
        this.videoElement = document.getElementById("webcam");
        this.canvasElement = document.getElementById("live-canvas");
        this.canvasCtx = this.canvasElement.getContext("2d");
        this.overlayImage = new Image();
        this.overlayImage.style.display = 'none'; // Keep it out of the DOM flow
        this.timeoutId = null; 

        this.pose = new Pose({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`,
        });

        this.pose.setOptions({
            modelComplexity: 1,
            smoothLandmarks: true,
            enableSegmentation: false,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5,
        });

        this.pose.onResults(this.onPoseResults.bind(this));

        this.camera = new Camera(this.videoElement, {
            onFrame: async () => {
                await this.pose.send({ image: this.videoElement });
            },
            width: 640,
            height: 480,
        });

        this.camera.start();
        this.startCloseTimer();
        console.log("Live Try-On session started.");
    }

    startCloseTimer() {
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
        this.timeoutId = setTimeout(() => {
            console.log("Auto-closing try-on session after 20 seconds of inactivity.");
            toggleWidgetsVisibility(false, false);
        }, 20000); // 20 seconds
    }

    setOverlay(imageUrl) {
        if (imageUrl) {
            this.overlayImage.src = imageUrl;
            this.overlayImage.style.display = 'block';
            this.startCloseTimer(); 
        } else {
            this.overlayImage.src = '';
            this.overlayImage.style.display = 'none';
        }
    }

    onPoseResults(results) {
        this.canvasCtx.save();
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
        this.canvasCtx.drawImage(results.image, 0, 0, this.canvasElement.width, this.canvasElement.height);

        if (results.poseLandmarks && this.overlayImage.src) {
            this.drawOverlay(results.poseLandmarks);
        }

        this.canvasCtx.restore();
    }

    drawOverlay(landmarks) {
        const leftShoulder = landmarks[11];
        const rightShoulder = landmarks[12];
        const leftHip = landmarks[23];
        const rightHip = landmarks[24];

        if (leftShoulder.visibility < 0.7 || rightShoulder.visibility < 0.7 ||
            leftHip.visibility < 0.7 || rightHip.visibility < 0.7) {
            return; // Not enough landmarks are visible
        }

        // --- All coordinates are in normalized screen space (0.0 - 1.0) ---
        const canvasWidth = this.canvasElement.width;
        const canvasHeight = this.canvasElement.height;

        // Calculate torso center
        const shoulderCenterX = (leftShoulder.x + rightShoulder.x) / 2;
        const hipCenterX = (leftHip.x + rightHip.x) / 2;
        const torsoCenterY = (leftShoulder.y + rightHip.y) / 2;
        
        // Calculate width and height based on torso
        const torsoWidth = Math.abs(leftShoulder.x - rightShoulder.x) * canvasWidth;
        const torsoHeight = Math.abs(leftShoulder.y - leftHip.y) * canvasHeight;

        // Add padding to make the clothing item look natural
        const widthPadding = 1.8; // Adjust this factor as needed
        const itemWidth = torsoWidth * widthPadding;
        const itemHeight = torsoHeight * 1.1; // Slightly longer than torso

        // Calculate rotation based on shoulder angle, and add PI to correct the inversion
        const angle = Math.atan2(rightShoulder.y - leftShoulder.y, rightShoulder.x - leftShoulder.x) + Math.PI;

        // --- Drawing on Canvas ---
        this.canvasCtx.save();
        // Translate and rotate canvas to draw the image
        this.canvasCtx.translate(shoulderCenterX * canvasWidth, torsoCenterY * canvasHeight);
        this.canvasCtx.rotate(angle);

        // Draw the image centered on the new, rotated origin
        this.canvasCtx.drawImage(
            this.overlayImage,
            -itemWidth / 2,
            -itemHeight / 2,
            itemWidth,
            itemHeight
        );

        this.canvasCtx.restore();
    }

    stop() {
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
        this.camera.stop();
        this.pose.close();
        console.log("Live Try-On session stopped.");
    }
}

// Schedule updates
updateTimeAndDate();
updateWeather();
updateNews();
updateCrypto();
updateCalendar();

setInterval(updateCalendar, 600000); // Refresh every 10 minutes
setInterval(updateTimeAndDate, 5000); // Update time every 5 second
setInterval(updateWeather, 300000); // Update weather every 5 minutes
setInterval(updateNews, 60000); // Update news every 10 minutes
setInterval(updateCrypto, 300000); // Update crypto prices every 5 minutes
