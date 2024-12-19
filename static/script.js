// Update Time and Date
function updateTimeAndDate() {
    fetch('/time_date')
        .then(response => response.json())
        .then(data => {
            document.getElementById('time').textContent = data.time;
            document.getElementById('date').textContent = data.date;
        });
}

// Update Weather
function updateWeather() {
    fetch('/weather')
        .then(response => response.json())
        .then(data => {
            document.getElementById('weather-description').textContent =
                `${data.weather[0].description}, ${data.main.temp}°C`;
            document.getElementById('weather-icon').src = data.weather[0].icon;
        });
}

// Update News
function updateNews() {
    fetch('/news')
        .then(response => response.json())
        .then(data => {
            document.getElementById('news').textContent =
                `News: ${data.articles[0].title}`;
        });
}

// Update Crypto Prices
function updateCrypto() {
    fetch('/crypto')
        .then(response => response.json())
        .then(data => {
            document.getElementById('crypto').textContent =
                `Bitcoin: $${data.bitcoin}, Ethereum: $${data.ethereum}`;
        });
}

// Poll Voice Responses
function pollVoiceResponse() {
    fetch('/voice_command')
        .then(response => response.json())
        .then(data => {
            if (data.response) {
                document.getElementById('voice-response').textContent = `Assistant: ${data.response}`;
            }
        })
        .catch(error => console.error('Error fetching voice response:', error));
}

// Update Calendar
function updateCalendar() {
    fetch('/calendar')
        .then(response => response.json())
        .then(data => {
            const calendarDiv = document.getElementById('calendar');
            if (data.error) {
                calendarDiv.textContent = "Failed to load calendar events.";
            } else if (data.message) {
                calendarDiv.textContent = data.message;
            } else if (data.length === 0) {
                calendarDiv.textContent = "No upcoming events.";
            } else {
                calendarDiv.innerHTML = data.map(event =>
                    `<div>${event.summary} - ${event.start.dateTime || event.start.date}</div>`
                ).join('');
            }
        })
        .catch(error => {
            console.error("Error fetching calendar:", error);
            document.getElementById('calendar').textContent = "Error loading calendar.";
        });
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
