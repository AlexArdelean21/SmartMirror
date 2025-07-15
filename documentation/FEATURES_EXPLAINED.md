
# Smart Mirror: Detailed Feature Explanation

This document provides a detailed technical explanation of some of the core features of the Smart Mirror application.

---

## 1. What is an API?

An **API (Application Programming Interface)** is a set of rules and protocols that allows different software applications to communicate with each other. It defines the methods and data formats that applications can use to request and exchange information.

Think of an API as a waiter in a restaurant. You (an application) don't need to know how the kitchen (another application or service) works. You just need to know the menu (the API's documentation) to place an order (make a request). The waiter (the API) takes your order to the kitchen and brings back the food (the response).

### How We Use APIs in This Project

Our Smart Mirror relies on APIs for much of its functionality. We use both **internal** and **external** APIs.

#### Internal API (Our Own Backend)

The Python Flask application (`app.py`) acts as a backend server that exposes its own set of API endpoints. The frontend (JavaScript running in the browser) calls these endpoints to fetch data and trigger actions.

**Examples of Internal API Endpoints:**

*   `GET /time_date`: Provides the current time and date.
*   `GET /weather`: Fetches weather data.
*   `GET /news`: Fetches the latest news headlines.
*   `POST /add_face`: Registers a new user's face.

#### External APIs (Third-Party Services)

Our backend services communicate with external, third-party APIs to get information from the wider internet.

**Examples of External APIs Used:**

*   **OpenWeatherMap API**: Used in `services/weather_service.py` to get real-time weather data for a specific location. We send a request with a location and our API key, and it returns weather conditions, temperature, etc.
*   **GNews API**: Used in `services/news_service.py` to fetch news articles from various sources. We send a query with topics of interest and it returns a list of relevant articles.
*   **CoinGecko API**: Used in `services/crypto_service.py` to get the latest prices for cryptocurrencies like Bitcoin and Ethereum.

---

## 2. WebSockets and Real-Time Communication

### What are WebSockets?

**WebSockets** provide a persistent, two-way communication channel between a client (the web browser) and a server. Unlike the traditional request-response model of HTTP, where the client always has to initiate a request, WebSockets allow the server to "push" information to the client at any time.

This is ideal for applications that require real-time updates, as it eliminates the need for the client to constantly poll the server for new data.

### How We Use WebSockets

We use the **Flask-SocketIO** library to implement WebSockets. This allows for seamless, real-time interaction between the user and the mirror.

#### Server-Side (`app.py` and services)

*   **Initialization**: In `util/socket_manager.py`, we create a global `socketio` object. In `app.py`, this object is initialized with our Flask app.
*   **Emitting Events**: The server can send messages (emit events) to the client. For example, after processing a voice command, `services/voice_service.py` might emit a `play_audio` event to make the mirror speak.
    ```python
    # Example from voice_utils.py
    socketio.emit("play_audio", {
        "audio_url": "path/to/audio.mp3",
        "text": "Hello, this is a response."
    })
    ```
*   **Listening for Events**: The server can also listen for events from the client. For instance, it listens for an `audio_finished` event to know when the mirror has finished speaking.
    ```python
    # From app.py
    @socketio.on('audio_finished')
    def handle_audio_finished():
        # Logic to handle audio completion
        pass
    ```

#### Client-Side (`static/script.js`)

*   **Connection**: The client connects to the WebSocket server as soon as the page loads.
    ```javascript
    const socket = io();
    ```
*   **Listening for Events**: The client listens for events from the server and reacts accordingly, for example by updating the UI or playing audio.
    ```javascript
    socket.on('play_audio', (data) => {
        // Code to play the audio file from data.audio_url
    });
    ```
*   **Emitting Events**: The client can also send events to the server.
    ```javascript
    // When audio playback is done
    audioElement.onended = () => {
        socket.emit('audio_finished');
    };
    ```

---

## 3. Facial Recognition

The facial recognition feature allows the Smart Mirror to identify registered users and load their personalized profiles and settings. The core logic is in `services/facial_recognition_service.py`.

### How It Works

The process relies on the `face_recognition` library, which is a powerful and easy-to-use wrapper around the dlib library.

1.  **Storing Known Faces**:
    *   When a new user is registered via the `add_face_vocally` function, the system captures a high-quality image of their face from the webcam.
    *   It then computes a **128-point facial encoding**—a unique numerical representation of the face's features.
    *   This encoding, along with the user's name, is saved into a file named `pictures/known_faces.pkl` using Python's `pickle` module for serialization.

2.  **Recognizing a Face**:
    *   The `recognize_faces_vocally` function is triggered to identify a user.
    *   It opens a video stream from the webcam (`cv2.VideoCapture`).
    *   For each frame, it performs the following steps:
        a.  **Detects Face Locations**: It uses `face_recognition.face_locations()` to find the coordinates (top, right, bottom, left) of any faces in the frame.
        b.  **Computes Encodings**: It generates a 128-point encoding for each detected face.
        c.  **Compares Faces**: It compares the newly generated encoding(s) against the list of all known encodings loaded from `known_faces.pkl`. The comparison is a mathematical calculation of the "distance" between the encodings.
        d.  **Finds a Match**: If the distance between the new face and a known face is below a certain `tolerance` (we use 0.5, a reasonably strict value), it is considered a match. The name associated with that known encoding is returned.
    *   If no face is found for 20 seconds, the process times out. If a face is found but doesn't match any known user, it returns "Unknown".

---

## 4. Pose Estimation for Virtual Try-On

Pose estimation is the technology behind our **Virtual Try-On** feature. It allows the mirror to detect a user's body posture in real-time and accurately overlay an image of a clothing item. This is handled entirely on the client-side in `static/script.js`.

### How It Works

We use **MediaPipe Pose**, a high-fidelity machine learning library from Google that runs directly in the browser.

1.  **Initialization**:
    *   When the virtual try-on feature is activated, a `LiveTryOn` class is instantiated in our JavaScript code.
    *   This class initializes MediaPipe's `Pose` model and sets up a `Camera` instance to get a video feed from the webcam.

2.  **Real-Time Processing**:
    *   The camera sends each video frame to the MediaPipe Pose model (`pose.send({image: videoElement})`).
    *   The model processes the image and returns a set of results, including the coordinates of **33 body landmarks** (e.g., shoulders, hips, elbows, knees).

3.  **Overlaying the Clothing**:
    *   The `onPoseResults` callback function is triggered every time MediaPipe has new results.
    *   Inside this function, we get the coordinates of key landmarks needed to position the clothing, such as the shoulders and hips.
    *   Using these landmarks, we calculate:
        a.  **Position**: The center point between the user's shoulders (`centerX`, `centerY`).
        b.  **Size**: The width is calculated based on the distance between the shoulder landmarks. This ensures the clothing scales realistically with the user's size and distance from the camera. The height is derived from the width while maintaining the overlay image's aspect ratio.
        c.  **Rotation (Implicit)**: While we don't do complex 3D rotation, the 2D position and size adjustments based on the landmark locations provide a convincing effect as the user moves.
    *   Finally, we use the HTML5 Canvas API's `drawImage()` method to render the clothing overlay image onto the canvas with the calculated position and dimensions, effectively "placing" it on the user.

---

## 5. Dynamic Background Themes

The mirror's background subtly changes its color scheme to reflect the current time of day, creating a more immersive and aesthetically pleasing experience. This is achieved with a clever combination of CSS and a small amount of JavaScript.

### How It Works

1.  **CSS Gradient and Animation**:
    *   In `static/style.css`, the `body` element has a large `linear-gradient` background. This gradient contains all four color schemes stacked vertically (e.g., night sky colors at the top, then morning, afternoon, and evening colors below).
    *   The `background-size` is set to be much larger vertically than the screen (`400%`).
    *   We use a CSS `transition` on the `background-position` property. This ensures that when the background position changes, it animates smoothly rather than jumping instantly.

2.  **Time-Based CSS Classes**:
    *   We define four simple CSS classes: `.theme-morning`, `.theme-afternoon`, `.theme-evening`, and `.theme-night`.
    *   Each class sets a different `background-position`, effectively "scrolling" the large gradient to show a different part of it.
        *   `.theme-night`: `background-position: 0 0;` (shows the top of the gradient)
        *   `.theme-morning`: `background-position: 0 33.33%;` (shows the sunrise part)
        *   And so on for afternoon and evening.

3.  **JavaScript Logic**:
    *   In `static/script.js`, the `updateTheme()` function runs once every minute.
    *   It gets the current hour of the day.
    *   Based on the hour, it adds the appropriate theme class to the `<body>` element (e.g., if it's 8 AM, it adds `.theme-morning`). It also removes any other theme classes to ensure only one is active at a time.

This combination allows us to create a dynamic and animated background with very efficient and simple code. 