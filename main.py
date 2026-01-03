import customtkinter as ctk
import threading
import datetime
import webbrowser
import yt_dlp
import speech_recognition as sr
import pyaudio
import os
import io
import asyncio
import edge_tts  # pip install edge_tts
from pydub import AudioSegment 
import firebase_admin
from firebase_admin import credentials, firestore
from groq import Groq
from dotenv import load_dotenv
# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Try to grab keys from environment if set
if os.getenv("GROQ_API_KEY"): GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- 1. CONNECT MEMORY ---
db = None
try:
    if os.path.exists("firebase_key.json"):
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("[SYSTEM] Connected to Firebase Memory.")
    else:
        print("[WARNING] No firebase_key.json. Memory disabled.")
except Exception as e:
    print(f"[ERROR] Memory Failed: {e}")

# --- 2. CONNECT BRAIN (GROQ) ---
try:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("[SYSTEM] Connected to Groq Brain.")
except Exception as e:
    print(f"[ERROR] Groq Failed: {e}")

# --- 3. THE FREE & GOOD VOICE (EDGE TTS) ---
def speak(text):
    """
    Uses Microsoft Edge's Free Neural Voice.
    Converts MP3 -> Raw Audio -> Plays on Speaker ID 4.
    """
    def _run():
        async def _get_audio():
            # VOICE CHOICES:
            # "en-US-GuyNeural" (Male, American)
            # "en-US-JennyNeural" (Female, American)
            # "en-GB-RyanNeural" (Male, British)
            communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
            
            # Create a memory buffer to hold the MP3 data
            mp3_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_data += chunk["data"]
            return mp3_data

        try:
            # 1. Get MP3 data from Edge (Async)
            mp3_bytes = asyncio.run(_get_audio())
            
            # 2. Convert MP3 -> PCM (Raw Audio) using pydub
            audio_segment = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
            
            # Resample to 24kHz to sound smooth
            audio_segment = audio_segment.set_frame_rate(24000).set_channels(1)
            pcm_data = audio_segment.raw_data

            # 3. Play via PyAudio (Speaker ID 4)
            p = pyaudio.PyAudio()
            stream = p.open(
                format=p.get_format_from_width(audio_segment.sample_width),
                channels=1, 
                rate=24000, 
                output=True, 
                output_device_index=4  # <--- YOUR SPEAKER ID
            )
            
            stream.write(pcm_data)
            stream.stop_stream()
            stream.close()
            p.terminate()

        except Exception as e:
            print(f"[VOICE ERROR] {e}")

    threading.Thread(target=_run).start()

# --- HELPER: YOUTUBE ---
def get_youtube_url(query):
    ydl_opts = {'format': 'best', 'noplaylist': True, 'quiet': True, 'default_search': 'ytsearch'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                return info['entries'][0]['webpage_url'], info['entries'][0]['title']
        except: return None, None
    return None, None

# --- GUI CLASS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class BuddyTwo(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Buddy 2.0 (Free & Smart)")
        self.geometry("800x600")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Chat Display
        self.chat_display = ctk.CTkTextbox(self, font=("Roboto Medium", 14), wrap="word")
        self.chat_display.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.chat_display.insert("0.0", "BUDDY: I'm online. Free and ready to chat!\n\n")
        self.chat_display.configure(state="disabled")

        # Input Field
        self.entry = ctk.CTkEntry(self, placeholder_text="Type or Click Mic...")
        self.entry.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.entry.bind("<Return>", self.send_command)

        # Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.place(relx=0.9, rely=0.92, anchor="center")
        
        self.mic_btn = ctk.CTkButton(self.btn_frame, text="🎤", width=40, height=40, command=self.activate_mic)
        self.mic_btn.pack(side="left", padx=5)

        self.send_btn = ctk.CTkButton(self.btn_frame, text="SEND", width=80, height=40, command=self.send_command)
        self.send_btn.pack(side="left")

    def log_to_gui(self, text, sender="BUDDY"):
        self.chat_display.configure(state="normal")
        timestamp = datetime.datetime.now().strftime("%H:%M")
        self.chat_display.insert("end", f"[{timestamp}] {sender}: {text}\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def activate_mic(self):
        self.mic_btn.configure(fg_color="green", text="👂")
        threading.Thread(target=self.listen_thread).start()

    def listen_thread(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            self.log_to_gui("Listening...", "SYSTEM")
            try:
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, timeout=5)
                command = r.recognize_google(audio)
                self.log_to_gui(f"Heard: {command}", "YOU")
                self.ask_groq(command)
            except Exception as e:
                self.log_to_gui(f"Voice Error: {e}", "SYSTEM")
            finally:
                self.mic_btn.configure(fg_color="#3B8ED0", text="🎤")

    def send_command(self, event=None):
        user_input = self.entry.get()
        if not user_input: return
        self.log_to_gui(user_input, "YOU")
        self.entry.delete(0, "end")
        threading.Thread(target=self.ask_groq, args=(user_input,)).start()

    def ask_groq(self, user_text):
        try:
            # 1. RETRIEVE MEMORY
            past_context = ""
            if db:
                try:
                    docs = db.collection('buddy_memory').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(3).stream()
                    history = []
                    for doc in docs:
                        d = doc.to_dict()
                        history.append(f"User said: {d['user']} | You replied: {d['bot']}")
                    past_context = "\n".join(history[::-1])
                except: pass

            # 2. CONSTRUCT PROMPT
            system_prompt = (
                f"You are Buddy 2.0. You have persistent memory.\n"
                f"RECENT CONVERSATION HISTORY:\n{past_context}\n\n"
                "INSTRUCTIONS:\n"
                "1. If user says PLAY song, reply: 'CMD: PLAY_YOUTUBE <query>'.\n"
                "2. If user says OPEN SITE, reply: 'CMD: OPEN_SITE <url>'.\n"
                "3. If user says GOOGLE, reply: 'CMD: GOOGLE_SEARCH <query>'.\n"
                "4. Keep answers short (1-2 sentences) and conversational."
            )

            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}],
                model="llama-3.1-8b-instant",
            )
            response = chat_completion.choices[0].message.content

            # 3. SAVE TO MEMORY
            if db:
                try:
                    db.collection('buddy_memory').add({
                        'user': user_text,
                        'bot': response,
                        'timestamp': datetime.datetime.now()
                    })
                except: pass

            # 4. EXECUTE ACTIONS
            if "CMD: PLAY_YOUTUBE" in response:
                query = response.replace("CMD: PLAY_YOUTUBE", "").strip()
                self.log_to_gui(f"Searching: {query}", "SYSTEM")
                speak(f"Okay, playing {query}")
                url, title = get_youtube_url(query)
                if url:
                    self.log_to_gui(f"Opening: {title}", "SYSTEM")
                    webbrowser.open(url)

            elif "CMD: GOOGLE_SEARCH" in response:
                query = response.replace("CMD: GOOGLE_SEARCH", "").strip()
                speak(f"Googling {query}")
                webbrowser.open(f"https://www.google.com/search?q={query}")

            elif "CMD: OPEN_SITE" in response:
                url = response.replace("CMD: OPEN_SITE", "").strip()
                speak("Opening website.")
                webbrowser.open(url)

            else:
                self.log_to_gui(response, "BUDDY")
                speak(response)

        except Exception as e:
            self.log_to_gui(f"Error: {str(e)}", "SYSTEM")

if __name__ == "__main__":
    app = BuddyTwo()
    app.mainloop()
