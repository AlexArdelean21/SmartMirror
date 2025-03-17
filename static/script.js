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
            let weatherDesc = document.getElementById('weather-description');
            let weatherIcon = document.getElementById('weather-icon');

            if (weatherDesc.textContent !== `${data.weather[0].description}, ${data.main.temp}°C`) {
                weatherDesc.textContent = `${data.weather[0].description}, ${data.main.temp}°C`;
                weatherDesc.classList.add('widget-update');
                setTimeout(() => weatherDesc.classList.remove('widget-update'), 300);
            }

            weatherIcon.src = data.weather[0].icon;
        });
}


// Update News
function updateNews() {
    fetch('/news')
        .then(response => response.json())
        .then(data => {
            let newsElement = document.getElementById('news');

            if (newsElement.textContent !== `News: ${data.articles[0].title}`) {
                newsElement.textContent = `News: ${data.articles[0].title}`;
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
            let cryptoElement = document.getElementById('crypto');

            let newCryptoText = `Bitcoin: $${data.bitcoin}, Ethereum: $${data.ethereum}`;
            if (cryptoElement.textContent !== newCryptoText) {
                cryptoElement.textContent = newCryptoText;
                cryptoElement.classList.add('widget-update');
                setTimeout(() => cryptoElement.classList.remove('widget-update'), 300);
            }
        });
}


// Poll Voice Responses and Update UI
function pollVoiceResponse() {
    fetch('/voice_command')
        .then(response => response.json())
        .then(data => {
            if (data.response_audio) {
                playSpeechAudio(data.response_audio);
                document.getElementById('voice-response').textContent = data.text;
            }
        })
        .catch(error => console.error('Error fetching voice response:', error));
}


// Voice Animation Using Web Audio API
const canvas = document.getElementById("voice-visualizer");
const ctx = canvas.getContext("2d");
canvas.width = 300;
canvas.height = 100;

let audioContext, analyzer, source, dataArray, bufferLength;

function startVoiceVisualizer(audioElement) {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyzer = audioContext.createAnalyser();
        analyzer.fftSize = 64; // Adjust for smoothness
        bufferLength = analyzer.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);
    }

    source = audioContext.createMediaElementSource(audioElement);
    source.connect(analyzer);
    analyzer.connect(audioContext.destination);

    drawVisualizer();
}

// Animate the Voice Response Based on Audio Frequency
function drawVisualizer() {
    requestAnimationFrame(drawVisualizer);
    analyzer.getByteFrequencyData(dataArray);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const barWidth = (canvas.width / bufferLength) * 1.5;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
        const barHeight = dataArray[i] / 2;
        ctx.fillStyle = `rgb(${barHeight + 100}, ${50 + i * 3}, 200)`;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 2;
    }
}

// Play Speech Audio and Start Animation
function playSpeechAudio(audioSrc) {
    const audio = new Audio(audioSrc);
    audio.play();
    startVoiceVisualizer(audio);

    audio.onended = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear visualizer when done
    };
}

// Update Calendar
function updateCalendar() {
    fetch('/calendar')
        .then(response => response.json())
        .then(data => {
            let calendarDiv = document.getElementById('calendar');

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

                if (calendarDiv.innerHTML !== newCalendarHTML) {
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


// Play Speech Audio and Start Animation
function playSpeechAudio(audioSrc) {
    const audio = new Audio(audioSrc);
    audio.play();
    startVoiceVisualizer(audio);

    // Show speaking animation
    document.getElementById('voice-response').textContent = "Smart Mirror is speaking...";

    audio.onended = () => {
        document.getElementById('voice-response').textContent = "Waiting for command...";
        ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear visualizer when done
    };
}


// Schedule updates
updateTimeAndDate();
updateWeather();
updateNews();
updateCrypto();
updateCalendar();

setInterval(updateCalendar, 600000); // Refresh every 10 minutes
setInterval(updateTimeAndDate, 1000); // Update time every second
setInterval(updateWeather, 600000); // Update weather every 10 minutes
setInterval(updateNews, 600000); // Update news every 10 minutes
setInterval(updateCrypto, 300000); // Update crypto prices every 5 minutes
setInterval(pollVoiceResponse, 15000); // Poll voice assistant every 15 seconds
