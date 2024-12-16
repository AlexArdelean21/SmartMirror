async function updateTimeDate() {
            const response = await fetch('/time_date');
            const data = await response.json();
            document.getElementById('time').innerText = data.time;
            document.getElementById('date').innerText = data.date;
        }

            async function updateWeather() {
        try {
            const response = await fetch('/weather');
            const data = await response.json();
            console.log('Weather Data:', data);

            if (data.error) {
                document.getElementById('weather-description').innerText = data.error;
                document.getElementById('weather-icon').style.display = 'none';
            } else if (data.main && data.weather) {
                const tempCelsius = data.main.temp;
                const description = data.weather[0].description;
                const icon = data.weather[0].icon;

                document.getElementById('weather-description').innerText = `${description}, ${tempCelsius}°C`;
                const iconElement = document.getElementById('weather-icon');
                iconElement.src = icon;
                iconElement.style.display = 'inline';
            } else {
                throw new Error('Invalid weather data structure');
            }
        } catch (error) {
            console.error('Error fetching weather data:', error);
            document.getElementById('weather-description').innerText = 'Error fetching weather data';
            document.getElementById('weather-icon').style.display = 'none';
        }
    }

        let newsIndex = 0;  // Track the current news index
        let newsArticles = [];

        async function updateNews() {
            try {
                const response = await fetch('/news');
                const data = await response.json();
                console.log('News Data:', data);

                if (data.articles && data.articles.length > 0) {
                    newsArticles = data.articles;
                    displayNextNews();  // Display the first article immediately
                } else {
                    document.getElementById('news').innerText = 'No news available';
                }
            } catch (error) {
                console.error('Error fetching news data:', error);
                document.getElementById('news').innerText = 'Error fetching news data';
            }
        }

        function displayNextNews() {
            if (newsArticles.length > 0) {
                const currentArticle = newsArticles[newsIndex];
                document.getElementById('news').innerText = currentArticle.title; // Simplified to show only the title
                newsIndex = (newsIndex + 1) % newsArticles.length;
            }
        }

        async function updateCrypto() {
            try {
                const response = await fetch('/crypto');
                const data = await response.json();
                console.log('Crypto Data:', data);

                if (data.error) {
                    document.getElementById('crypto').innerText = data.error;
                } else {
                    const bitcoin = `Bitcoin: $${data.bitcoin}`;
                    const ethereum = `Ethereum: $${data.ethereum}`;
                    document.getElementById('crypto').innerText = `${bitcoin} | ${ethereum}`;
                }
            } catch (error) {
                console.error('Error fetching crypto data:', error);
                document.getElementById('crypto').innerText = 'Error fetching cryptocurrency prices';
            }
        }

        // Initial Updates
        updateTimeDate();
        updateWeather();
        updateNews();
        updateCrypto();

        // Adjusted Intervals
        setInterval(updateTimeDate, 1000);       // Update time every second
        setInterval(updateWeather, 300000);     // Update weather every 5 minutes
        setInterval(updateNews, 300000);        // Fetch new articles every 5 minutes
        setInterval(displayNextNews, 10000);    // Cycle news every 10 seconds
        setInterval(updateCrypto, 60000);       // Update cryptocurrency prices every 1 minute