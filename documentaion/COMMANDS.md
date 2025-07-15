# Smart Mirror Voice Commands

This document provides a comprehensive list of all the voice commands that can be used to interact with the smart mirror.

---

## General Commands

These commands can be used at almost any time.

| Command | Description |
| :--- | :--- |
| **"Hey Adonis"** | The wake word. Say this first to activate the assistant and begin giving commands. |
| **"Stop"** | Immediately interrupts whatever the assistant is doing. This is useful for stopping a long audio response or dismissing the virtual try-on feature. |
| **"That's all"** / **"No"** | Ends the current conversation and puts the assistant back into sleep mode, waiting for the next wake word. |

---

## Information Widgets

These commands are used to get real-time information.

| Command | Example Phrases | Description |
| :--- | :--- | :--- |
| **Weather** | "What's the weather?" <br/> "Tell me the weather." | Fetches and displays the current weather for the user's configured location. |
| **News** | "Give me the news." <br/> "What's the latest news?" | Fetches and displays the latest news headlines based on the user's preferred topics. |
| **Crypto Prices** | "Tell me crypto prices." <br/> "What's the price of crypto?" | Fetches and displays the current prices for Bitcoin and Ethereum. |
| **Time & Date** | "What time is it?" <br/> "What's the date?" | Displays the current time and date. |

---

## Calendar Management

These commands interact with the user's Google Calendar. *Note: This feature is currently configured to work only for the user "Alex".*

| Command | Example Phrases | Description |
| :--- | :--- | :--- |
| **Check Events** | "Do I have any plans?" <br/> "Do I have any events today?" | Fetches and reads out the user's next 5 upcoming calendar events. |
| **Add Event** | "Add an event called *meeting* tomorrow at *3 PM*." <br/> "Add an event called *lunch* today at *12:30*." <br/> "Add a meeting tomorrow at 10." | Creates a new event in the user's calendar. The system parses the event name, date, and time from the command. |

---

## User & Profile Management

These commands are related to user identification and profiles.

| Command | Example Phrases | Description |
| :--- | :--- | :--- |
| **Add Face** | "Add my face." | Initiates the facial recognition enrollment process to register a new user with the system. |
| **Recognize Face**| "Start facial recognition." | Manually triggers the facial recognition process to identify the current user. (This also happens automatically after the wake word is detected). |

---

## Virtual Try-On

These commands control the virtual clothing try-on feature. This is the most complex set of commands with several combinations.

### Initiating a Try-On Session

The core command follows a flexible structure. You can combine a category, color, and/or price.

-   **Base Command:** "I want to try on..."
-   **Supported Categories:** "men's clothing" (default), "women's clothing"
-   **Supported Colors:** `red`, `blue`, `black`, `white`, `green`, `yellow`, `brown`
-   **Price:** "...under `[X]` dollars"

| Example Combination | Description |
| :--- | :--- |
| "I want to try on a **shirt**." | Shows the top 3 items from the default category ("men's clothing"). |
| "I want to try on a **black shirt**." | Shows shirts that have "black" in their title. |
| "I want to try on a **blue jacket**." | Shows jackets that have "blue" in their title. |
| "I want to try on a **women's jacket**."| Shows the top 3 items from the "women's clothing" category. |
| "I want to try on a **red dress under 50 dollars**." | Shows red dresses from the "women's clothing" category that cost less than $50. |

### Interacting with Try-On Options

Once the clothing options are displayed on the screen, you can use these commands.

| Command | Example Phrases | Description |
| :--- | :--- | :--- |
| **Select Item** | "Try on **option one**." <br/> "Select the **second** one." <br/> "Let me see the **third** option." | Selects one of the displayed items to render over your video feed. |
| **Dismiss** | "Stop" | Hides the try-on interface and returns the mirror to its normal state. |

---

## AI Assistant & Recommendations

These commands leverage the OpenAI GPT integration for more dynamic and conversational responses.

| Command | Example Phrases | Description |
| :--- | :--- | :--- |
| **Recommendations** | "What should I wear?" <br/> "Give me a recommendation." <br/> "Do you have any advice for me?" | Uses the AI model to generate a personal recommendation based on your calendar, the weather, and the time of day. |
| **General Conversation**| "Tell me a joke." <br/> "Explain quantum computing." <br/> "How are you?" | Any command that does not match the specific functions above will be sent to the AI for a conversational response. 