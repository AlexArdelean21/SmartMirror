let previousWeather = "";
let previousNews = "";
let previousCrypto = "";
let previousCalendar = "";
const socket = io();

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

socket.on("play_audio", (data) => {
    console.log("🔊 [Socket] Received voice playback:", data);
    playSpeechAudio(data.audio_url);
    document.getElementById("voice-text").textContent = data.text;
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
//setInterval(pollVoiceResponse, 15000); // Poll voice assistant every 15 seconds
//pollVoiceResponse();