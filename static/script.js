let previousWeather = "";
let previousNews = "";
let previousCrypto = "";
let previousCalendar = "";
const socket = io();
let currentTryOnItems = [];
let poseDetector = null;
let webcamStream = null;

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
    const canvas = document.getElementById('voice-visualizer');
    const ctx = canvas.getContext('2d');
    const voiceBox = document.getElementById('voice-response');
    if (!audioUrl) {
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
            drawSineWave();
        })
        .catch(error => {});
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

            document.getElementById("tryon-options").style.display = "block";
            toggleWidgetsVisibility(true);
            setTimeout(() => {
                toggleWidgetsVisibility(false);
                console.log("Auto-hide triggered: try-on options removed after 20s.");
            }, 30000); // 30 seconds

        })
        .catch(error => console.error("Error loading try-on options:", error));
}


function toggleWidgetsVisibility(showTryOn = true) {
    const widgetsToToggle = ['weather', 'news', 'crypto', 'calendar'];

    widgetsToToggle.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.style.display = showTryOn ? 'none' : 'flex';
        }
    });

    const tryOnWidget = document.getElementById('tryon-options');
    if (tryOnWidget) {
        tryOnWidget.style.display = showTryOn ? 'block' : 'none';
    }
}

async function initializeWebcam() {
    try {
        const video = document.getElementById('webcam-feed');
        webcamStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: 300,
                height: 400,
                facingMode: 'user'
            } 
        });
        video.srcObject = webcamStream;
        // Initialize pose detector using BlazePose with CDN solutionPath
        poseDetector = await poseDetection.createDetector(
            poseDetection.SupportedModels.BlazePose,
            {
                runtime: 'mediapipe',
                modelType: 'full',
                solutionPath: 'https://cdn.jsdelivr.net/npm/@mediapipe/pose'
            }
        );
        // Start pose detection
        detectPose();
    } catch (error) {
        console.error('Error accessing webcam:', error);
    }
}

async function detectPose() {
    if (!poseDetector) return;
    
    const video = document.getElementById('webcam-feed');
    const poses = await poseDetector.estimatePoses(video);
    
    if (poses.length > 0) {
        const pose = poses[0];
        updateOverlayPosition(pose);
    }
    
    // Continue detection
    requestAnimationFrame(detectPose);
}

function updateOverlayPosition(pose) {
    const overlay = document.getElementById('overlay-item');
    const video = document.getElementById('webcam-feed');
    if (!overlay || !video) return;

    // DEBUG: Log all keypoints
    if (pose && pose.keypoints) {
        console.log('Pose keypoints:', pose.keypoints);
    }

    // Support both snake_case and camelCase keypoint names
    function getKeypoint(name1, name2) {
        return pose.keypoints.find(kp => kp.name === name1 || kp.name === name2);
    }
    const leftShoulder = getKeypoint('left_shoulder', 'leftShoulder');
    const rightShoulder = getKeypoint('right_shoulder', 'rightShoulder');
    const leftHip = getKeypoint('left_hip', 'leftHip');
    const rightHip = getKeypoint('right_hip', 'rightHip');

    if (leftShoulder && rightShoulder && leftHip && rightHip) {
        // Calculate chest center
        const centerX = (leftShoulder.x + rightShoulder.x) / 2;
        const centerY = (leftShoulder.y + rightShoulder.y) / 2;
        // Calculate width (shoulder to shoulder)
        const shoulderDist = Math.abs(rightShoulder.x - leftShoulder.x);
        // Calculate height (shoulder to hip average)
        const avgHipY = (leftHip.y + rightHip.y) / 2;
        const chestHeight = avgHipY - centerY;
        // Scaling factors for realism
        const width = shoulderDist * 1.35; // even wider for realism
        const height = chestHeight * 1.3;  // even longer for realism
        // Position overlay so it's centered horizontally and starts at shoulders
        overlay.style.position = 'absolute';
        overlay.style.left = `${centerX - width / 2}px`;
        overlay.style.top = `${centerY}px`;
        overlay.style.width = `${width}px`;
        overlay.style.height = `${height}px`;
        overlay.style.maxWidth = '';
        overlay.style.maxHeight = '';
        overlay.style.transform = '';
    } else {
        // Fallback: center overlay
        overlay.style.position = 'absolute';
        overlay.style.left = '50%';
        overlay.style.top = '50%';
        overlay.style.transform = 'translate(-50%, -50%)';
        overlay.style.width = '80%';
        overlay.style.height = '80%';
        overlay.style.maxWidth = '';
        overlay.style.maxHeight = '';
    }
}

function showStaticOverlay(imageUrl) {
    const overlay = document.getElementById("overlay-item");
    overlay.src = imageUrl;

    // Hide all widgets except time, voice visualizer, and tryon-preview
    document.querySelectorAll('.widget').forEach(el => {
        if (!el.id.match(/^(time-widget|voice-response|tryon-preview)$/)) {
            el.style.display = 'none';
        }
    });
    document.getElementById("tryon-preview").style.display = "block";
    // Hide and clear try-on options
    const tryonOptions = document.getElementById("tryon-options");
    tryonOptions.style.display = "none";
    const productOptions = document.getElementById("product-options");
    if (productOptions) productOptions.innerHTML = '';

    // Remove overlay max size restrictions
    overlay.style.maxWidth = '';
    overlay.style.maxHeight = '';

    setTimeout(() => {
        document.getElementById("tryon-preview").style.display = "none";
        // Restore all widgets
        document.querySelectorAll('.widget').forEach(el => {
            if (!el.id.match(/^(tryon-preview)$/)) {
                el.style.display = '';
            }
        });
        // Stop webcam stream when hiding
        if (webcamStream) {
            webcamStream.getTracks().forEach(track => track.stop());
            webcamStream = null;
        }
    }, 20000);

    // Initialize webcam if not already initialized
    setTimeout(() => {
        if (!webcamStream) {
            initializeWebcam();
        }
    }, 100);
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
        toggleWidgetsVisibility(false);
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
        showStaticOverlay(item.image_url);
    } else {
        console.warn("No item found for selected index:", index);
    }
});

    const { category, color, max_price } = data;
    showTryOnOptions(category, color, max_price);
});



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
