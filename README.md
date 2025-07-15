# AI-Powered Smart Mirror

This is an AI-powered Smart Mirror that provides a range of intelligent services through a modern, voice-controlled interface. It features personalized user profiles, real-time information widgets, and an advanced virtual try-on system.

## ✨ Core Features

The smart mirror is designed to be a central hub for your daily information needs, offering the following features:

-   **🗣️ Voice-Controlled Interface:** Hands-free control using the "Hey Adonis" wake word, with natural language understanding for commands and conversation.
-   **👤 Personalized User Profiles:** Uses facial recognition to identify users and load their preferences, including location, news topics, and calendar access.
-   **☀️ Dynamic Information Widgets:** A clean, modern interface displaying:
    -   Current Time & Date
    -   Live Weather Updates
    -   Latest News Headlines
    -   Cryptocurrency Prices (Bitcoin & Ethereum)
    -   Upcoming Google Calendar Events
-   **🤖 AI Assistant:** Integrated with OpenAI's GPT models to provide conversational answers to general questions and generate personalized recommendations.
-   **👕 Virtual Try-On:** An advanced feature that allows users to realistically try on clothing items using real-time pose estimation.

## 👕 Virtual Try-On System

The virtual try-on feature is a key component of the smart mirror, with several advanced capabilities:

-   **Advanced Pose Estimation:** Integrates MediaPipe Pose for real-time body tracking with confidence scoring and smoothing to reduce jitter.
-   **Clothing-Specific Behavior:** Uses category-aware positioning to correctly place different types of clothing, such as jackets, shirts, pants, and dresses.
-   **Realistic Rendering:** Applies multi-layered shadow effects and anti-aliasing to create a more realistic and immersive overlay.
-   **Background Removal:** Automatically removes the background from product images to ensure a clean overlay.

## 🛠️ Technical Implementation

-   **Backend:** Python with **Flask** for the web server and API, and **Flask-SocketIO** for real-time WebSocket communication.
-   **Frontend:** Vanilla JavaScript (ES6+) for logic, **MediaPipe** for pose detection, and **Socket.IO** client for real-time updates.
-   **Voice & AI:**
    -   **`pvporcupine`** for wake word detection.
    -   **`SpeechRecognition`** for command transcription.
    -   **Google Cloud Text-to-Speech** for audio responses.
    -   **OpenAI GPT** for conversational AI.
-   **Data & Services:**
    -   **`face_recognition`** for user identification.
    -   **`rembg`** for image background removal.
    -   APIs for Weather, News, and Crypto data.

## 📄 Project Structure

A detailed explanation of every file and directory in this project is available in the `PROJECT_STRUCTURE.md` file. This document provides a complete overview of the codebase architecture.

## 🚀 Installation & Setup

### Prerequisites
-   Python 3.8+
-   Webcam access
-   A modern web browser (Chrome recommended)
-   API keys for Google Cloud, OpenAI, NewsAPI, and OpenWeatherMap.

### Setup Instructions
1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    -   Create a `.env` file in the root directory.
    -   Add your API keys and configuration to this file. See `PROJECT_STRUCTURE.md` for details on the required variables.

4.  **Run the application:**
    ```bash
    python app.py
    ```
5.  Open your web browser and navigate to `http://localhost:5000`.

## 🎯 Usage

The primary way to interact with the mirror is through voice commands.

1.  **Activation:** The mirror is activated by saying the wake word: **"Hey Adonis"**.
2.  **Facial Recognition:** After activation, it will use the camera to recognize the user and load their profile.
3.  **Commands:** Once a user is logged in, you can issue commands like:
    -   *"What's the weather?"*
    -   *"Give me the news."*
    -   *"Do I have any plans today?"*
    -   *"Add an event called meeting tomorrow at 3 PM."*
    -   *"I want to try on a black shirt."*
    -   *"Tell me a joke."* (for the AI assistant)

You can also interrupt the assistant at any time by saying **"Stop"**. 