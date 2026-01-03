
```markdown
# Buddy 2.0 - AI Desktop Assistant (Linux Version) 🤖🐧

Buddy 2.0 is a smart, voice-activated desktop assistant built for Linux (Ubuntu). It combines a fast LLM brain with high-quality free voice synthesis and persistent memory.

## 🚀 Features
* **Brain:** Uses **Groq Cloud** (Llama 3) for instant responses.
* **Voice:** Uses **Edge TTS** (Microsoft Neural Voice) for high-quality, free speech.
* **Memory:** Uses **Firebase Firestore** to remember past conversations.
* **Ears:** Uses `SpeechRecognition` to listen to your commands.
* **GUI:** Modern interface built with `CustomTkinter`.

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/paulmicky1/Buddy2.0.git](https://github.com/paulmicky1/Buddy2.0.git)
cd Buddy2.0

```

### 2. Install System Dependencies

Update your package manager and install the necessary audio and GUI libraries.

```bash
sudo apt update
sudo apt install ffmpeg portaudio19-dev python3-tk

```

### 3. Set Up Virtual Environment

Create a virtual environment to manage dependencies securely.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it (You must do this every time you open a new terminal)
source venv/bin/activate

```

### 4. Install Python Libraries

Install the required packages listed in `requirements.txt`.

```bash
pip install -r requirements.txt

```

### 5. Configure Environment Variables

You need to create a `.env` file to store your API key.

1. Open the file editor:
```bash
nano .env

```


2. Add your Groq API key:
```text
GROQ_API_KEY="gsk_YOUR_ACTUAL_KEY_HERE"

```


3. Save and exit (Press `CTRL+O`, `Enter`, then `CTRL+X`).

## ▶️ Usage

To start Buddy 2.0, make sure your virtual environment is active and run the main script.

```bash
# Activate environment (if not already active)
source venv/bin/activate

# Run the assistant
python3 main.py

```

