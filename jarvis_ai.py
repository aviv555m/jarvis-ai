import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import pyttsx3
import requests
import os
import webbrowser
import logging
import speech_recognition as sr
from queue import Queue
import subprocess
import spotipy
from spotipy import SpotifyOAuth
import psutil
import keyboard
from plyer import notification
import pygame  # for audio visualization
import json
import platform
from datetime import datetime, timedelta

# === CONFIG ===
OLLAMA_MODEL = "llama3"
OLLAMA_URL = "http://localhost:11434/api/generate"
CHAT_HISTORY_LIMIT = 10
TRIGGER_WORD = "jarvis"
CONVERSATION_TIMEOUT = 30

SPOTIPY_CLIENT_ID = 'your_client_id'
SPOTIPY_CLIENT_SECRET = 'your_client_secret'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8000/callback'

VOICE_AUTH_ENABLED = True
AUTHORIZED_USER_PHRASE = ""  # simple passphrase

# Language support (English and Spanish example)
LANGUAGES = {
    "en": {
        "yes_sir": "Yes sir?",
        "shutting_down": "Shutting down your PC.",
        "open_youtube": "Opening YouTube.",
        "open_whatsapp": "Opening WhatsApp Web.",
        "open_notepad": "Opening Notepad.",
        "closing_notepad": "Closing Notepad.",
        "open_spotify": "Opening Spotify.",
        "close_spotify": "Closing Spotify.",
        "open_discord": "Opening discord.",
        "close_discord": "Closing discord.",
        "no_spotify_device": "No Spotify device available. Open Spotify on one of your devices.",
        "spotify_error": "Sorry, there was an error playing the song.",
        "no_active_spotify_device": "No active Spotify device found.",
        "paused_spotify": "Paused Spotify.",
        "resumed_spotify": "Resumed Spotify.",
        "next_track": "Skipping to next track.",
        "previous_track": "Going to previous track.",
        "loop_track": "Looping current track.",
        "stop_loop": "Stopped looping.",
        "shuffle_on": "Turned on shuffle.",
        "shuffle_off": "Turned off shuffle.",
        "time_is": "It is ",
        "joke": "Why did the computer go to therapy? Because it had too many bytes.",
        "searching_google": "Searching Google for ",
        "conversation_timeout": "Conversation timed out. Say 'Jarvis' to wake me again.",
        "listening_wake": "🎤 Listening for wake word...",
        "listening_command": "🎤 Listening for command...",
        "unrecognized_speech": "❓ Unrecognized speech.",
        "command_timeout": "⏳ Command timeout.",
        "tts_error": "Sorry, I had trouble speaking.",
        "ai_error": "Sorry, I couldn't reach the local AI model.",
        "unauthorized": "You are not authorized to use Jarvis.",
        "reminder_set": "Reminder set for ",
        "volume_up": "Volume increased.",
        "volume_down": "Volume decreased.",
        "volume_muted": "Volume muted.",
        "volume_unmuted": "Volume unmuted.",
        "reminder_alert": "Reminder!",
        "personalities": {
            "formal": "I will respond formally.",
            "casual": "I'll keep it casual.",
            "humorous": "Let's have some fun with humor!"
        },
        "personality_set": "Personality set to ",
        "language_set": "Language switched to English."
    },
    "es": {
        "yes_sir": "Sí señor?",
        "shutting_down": "Apagando tu PC.",
        "open_youtube": "Abriendo YouTube.",
        "open_whatsapp": "Abriendo WhatsApp Web.",
        "open_notepad": "Abriendo el Bloc de notas.",
        "closing_notepad": "Cerrando el Bloc de notas.",
        "open_spotify": "Abriendo Spotify.",
        "close_spotify": "Cerrando Spotify.",
        "open_discord": "Abriendo Discord.",
        "close_discord": "Cerrando Discord.",
        "no_spotify_device": "No hay dispositivo Spotify disponible. Abre Spotify en uno de tus dispositivos.",
        "spotify_error": "Lo siento, hubo un error al reproducir la canción.",
        "no_active_spotify_device": "No se encontró dispositivo activo de Spotify.",
        "paused_spotify": "Spotify en pausa.",
        "resumed_spotify": "Spotify reanudado.",
        "next_track": "Saltando a la siguiente canción.",
        "previous_track": "Volviendo a la canción anterior.",
        "loop_track": "Repitiendo la canción actual.",
        "stop_loop": "Dejé de repetir.",
        "shuffle_on": "Modo aleatorio activado.",
        "shuffle_off": "Modo aleatorio desactivado.",
        "time_is": "Son las ",
        "joke": "¿Por qué la computadora fue a terapia? Porque tenía demasiados bytes.",
        "searching_google": "Buscando en Google ",
        "conversation_timeout": "La conversación terminó. Di 'Jarvis' para despertarme de nuevo.",
        "listening_wake": "🎤 Escuchando la palabra de activación...",
        "listening_command": "🎤 Escuchando comando...",
        "unrecognized_speech": "❓ No entendí lo que dijiste.",
        "command_timeout": "⏳ Tiempo de espera agotado para el comando.",
        "tts_error": "Lo siento, tuve problemas para hablar.",
        "ai_error": "Lo siento, no pude comunicarme con el modelo AI local.",
        "unauthorized": "No estás autorizado para usar Jarvis.",
        "reminder_set": "Recordatorio establecido para ",
        "volume_up": "Volumen aumentado.",
        "volume_down": "Volumen disminuido.",
        "volume_muted": "Volumen silenciado.",
        "volume_unmuted": "Volumen activado.",
        "reminder_alert": "¡Recordatorio!",
        "personalities": {
            "formal": "Responderé formalmente.",
            "casual": "Responderé de manera informal.",
            "humorous": "¡Vamos a divertirnos con humor!"
        },
        "personality_set": "Personalidad establecida a ",
        "language_set": "Idioma cambiado a español."
    }
}

CURRENT_LANGUAGE = "en"
P = LANGUAGES[CURRENT_LANGUAGE]

# === Global Variables ===
external_command_queue = Queue()
chat_history = []
personality_mode = "casual"
volume_muted = False
reminders = []

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Initialize pyttsx3 once ===
'''
engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.setProperty('volume', 1.0)
'''
def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.setProperty('volume', 1.0)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logging.error(f"TTS error: {e}")


# === Spotify Setup ===
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-read-playback-state,user-modify-playback-state,user-read-currently-playing,playlist-modify-public,playlist-modify-private"
))

def get_available_device():
    devices = sp.devices()
    for d in devices['devices']:
        if d['is_active']:
            return d['id']
    if devices['devices']:
        return devices['devices'][0]['id']
    return None

def play_spotify_song(song_name):
    try:
        query = song_name.strip()
        # Optionally add market param here, e.g. market='US'
        results = sp.search(q=query, type='track', limit=5)
        tracks = results.get('tracks', {}).get('items', [])
        if not tracks:
            return f"Couldn't find '{song_name}' on Spotify."

        # Log top 5 candidates for debugging
        logging.info("Top 5 search results:")
        for i, t in enumerate(tracks):
            logging.info(f"{i+1}: {t['name']} by {t['artists'][0]['name']}")

        # Pick the best match (first)
        track_uri = tracks[0]['uri']
        device_id = get_available_device()
        if not device_id:
            return "No Spotify device available. Open Spotify on one of your devices."

        sp.start_playback(device_id=device_id, uris=[track_uri])
        return f"Playing {tracks[0]['name']} by {tracks[0]['artists'][0]['name']}."

    except Exception as e:
        logging.error(f"Spotify error: {e}")
        return "Sorry, there was an error playing the song."


def control_spotify(command):
    try:
        device_id = get_available_device()
        if not device_id:
            return P["no_active_spotify_device"]

        cmd = command.lower()

        if "pause" in cmd or "stop" in cmd:
            sp.pause_playback(device_id=device_id)
            return P["paused_spotify"]
        elif "start" in cmd or "resume" in cmd:
            sp.start_playback(device_id=device_id)
            return P["resumed_spotify"]
        elif "next" in cmd:
            sp.next_track(device_id=device_id)
            return P["next_track"]
        elif "previous" in cmd or "back" in cmd:
            sp.previous_track(device_id=device_id)
            return P["previous_track"]
        elif "stop" in cmd and "loop" in cmd:
            sp.repeat("off", device_id=device_id)
            return P["stop_loop"]
        elif "loop" in cmd:
            sp.repeat("track", device_id=device_id)
            return P["loop_track"]
        elif "shuffle" in cmd and "off" in cmd:
            sp.shuffle(False, device_id=device_id)
            return P["shuffle_off"]
        elif "shuffle" in cmd:
            sp.shuffle(True, device_id=device_id)
            return P["shuffle_on"]
        else:
            return None
    except Exception as e:
        logging.error(f"Spotify control error: {e}")
        return "Failed to control Spotify."

# === Speech Recognition Setup ===
recognizer = sr.Recognizer()
mic = sr.Microphone()

# === GUI Setup ===
root = tk.Tk()
root.title("Jarvis Assistant")
root.geometry("700x600")
root.configure(bg="#1e1e1e")

# Chat output area
chat_box = scrolledtext.ScrolledText(root, bg="#1e1e1e", fg="white", font=("Consolas", 12), wrap="word", state='disabled')
chat_box.pack(expand=True, fill="both", padx=5, pady=5)

# Manual input frame
input_frame = tk.Frame(root, bg="#1e1e1e")
input_frame.pack(fill="x", padx=5, pady=5)

entry = tk.Entry(input_frame, bg="#333", fg="white", font=("Consolas", 12))
entry.pack(side="left", expand=True, fill="x", padx=5, pady=5)

send_button = tk.Button(input_frame, text="Send", command=lambda: on_enter(), bg="#444", fg="white")
send_button.pack(side="right", padx=5)

# Debug panel frame
debug_frame = tk.Frame(root, bg="#121212", height=100)
debug_frame.pack(fill="x", padx=5, pady=5)

debug_label = tk.Label(debug_frame, text="Debug Panel (Speech recognition & AI responses):", bg="#121212", fg="white")
debug_label.pack(anchor='w')

debug_box = tk.Text(debug_frame, bg="#222", fg="lightgreen", height=5, font=("Consolas", 10), state='disabled')
debug_box.pack(fill="x", padx=5, pady=2)

# Personality / language controls
control_frame = tk.Frame(root, bg="#1e1e1e")
control_frame.pack(fill="x", padx=5, pady=5)

personality_var = tk.StringVar(value=personality_mode)
language_var = tk.StringVar(value=CURRENT_LANGUAGE)

def set_personality_mode():
    global personality_mode
    personality_mode = personality_var.get()
    response = P["personalities"].get(personality_mode, "Personality mode set.")
    update_gui("Jarvis", response)
    speak(response)

def set_language():
    global CURRENT_LANGUAGE, P
    CURRENT_LANGUAGE = language_var.get()
    P = LANGUAGES[CURRENT_LANGUAGE]
    update_gui("System", P["language_set"])
    speak(P["language_set"])

tk.Label(control_frame, text="Personality:", bg="#1e1e1e", fg="white").pack(side="left")
tk.OptionMenu(control_frame, personality_var, "formal", "casual", "humorous", command=lambda _: set_personality_mode()).pack(side="left", padx=5)

tk.Label(control_frame, text="Language:", bg="#1e1e1e", fg="white").pack(side="left", padx=10)
tk.OptionMenu(control_frame, language_var, *LANGUAGES.keys(), command=lambda _: set_language()).pack(side="left", padx=5)

# Audio visualization setup (pygame mixer)
pygame.mixer.init()
audio_visualizer_running = False

def update_gui(role, message):
    def inner():
        chat_box.config(state='normal')
        chat_box.insert("end", f"{role}: {message}\n")
        chat_box.see("end")
        chat_box.config(state='disabled')

        debug_box.config(state='normal')
        if role in ("You", "Jarvis"):
            debug_box.insert("end", f"{role}: {message}\n")
            debug_box.see("end")
        debug_box.config(state='disabled')
    root.after(0, inner)

def on_enter(event=None):
    cmd = entry.get()
    if cmd.strip():
        update_gui("You", cmd)
        handle_command(cmd)
        entry.delete(0, 'end')

entry.bind("<Return>", on_enter)

# === System Command Handler ===
def try_system_command(text):
    lowered = text.lower()

    if "self destruct" in lowered:
        self_destruct()

    # Voice authentication (basic)
    if VOICE_AUTH_ENABLED and not is_authorized(lowered):
        return P["unauthorized"]

    # Play song on Spotify
    if ("play song" in lowered or ("play" in lowered and "spotify" in lowered)):
        song_name = lowered.split("play")[-1].replace("on spotify", "").strip()
        return play_spotify_song(song_name)

    # Spotify controls
    spotify_control = control_spotify(lowered)
    if spotify_control:
        return spotify_control

    # Volume controls (Windows only)
    if "volume up" in lowered:
        change_volume(5)
        return P["volume_up"]
    elif "volume down" in lowered:
        change_volume(-5)
        return P["volume_down"]
    elif "mute volume" in lowered or "volume mute" in lowered:
        mute_volume(True)
        return P["volume_muted"]
    elif "unmute volume" in lowered:
        mute_volume(False)
        return P["volume_unmuted"]

    # Open/close common apps
    if "shut down" in lowered:
        confirm_and_shutdown()
        return P["shutting_down"]

    elif "open youtube" in lowered:
        webbrowser.open("https://youtube.com")
        return P["open_youtube"]

    elif "open whatsapp" in lowered:
        webbrowser.open("https://web.whatsapp.com")
        return P["open_whatsapp"]

    elif "open notepad" in lowered:
        subprocess.Popen(["notepad.exe"])
        return P["open_notepad"]

    elif "close notepad" in lowered:
        kill_process("notepad.exe")
        return P["closing_notepad"]

    elif "open spotify" in lowered:
        try:
            subprocess.Popen([r"C:\\Users\\avivm\\AppData\\Roaming\\Spotify\\Spotify.exe"])
        except FileNotFoundError:
            return "Spotify not found."
        return P["open_spotify"]

    elif "close spotify" in lowered:
        kill_process("spotify.exe")
        return P["close_spotify"]

    elif "open discord" in lowered:
        try:
            subprocess.Popen([r"C:\\Users\\avivm\\AppData\\Local\\Discord\\Update.exe", "--processStart", "Discord.exe"])
        except FileNotFoundError:
            return "Discord not found."
        return P["open_discord"]

    elif "close discord" in lowered:
        kill_process("discord.exe")
        return P["close_discord"]

    elif "open calculator" in lowered:
        if platform.system() == "Windows":
            subprocess.Popen("calc.exe")
            return "Opening Calculator."
        else:
            return "Calculator open command not supported on your OS."

    # System info queries
    elif "cpu usage" in lowered:
        usage = psutil.cpu_percent()
        return f"Current CPU usage is {usage}%."

    elif "ram usage" in lowered:
        usage = psutil.virtual_memory().percent
        return f"Current RAM usage is {usage}%."

    elif "battery status" in lowered:
        battery = psutil.sensors_battery()
        if battery:
            return f"Battery is at {battery.percent}%."
        else:
            return "Battery information not available."

    elif "what time is it" in lowered or "current time" in lowered:
        return P["time_is"] + time.strftime("%H:%M")

    elif "tell me a joke" in lowered:
        return P["joke"]

    elif "search google for" in lowered:
        query = lowered.split("search google for")[-1].strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return P["searching_google"] + query

    # Weather info
    elif "weather" in lowered:
        city = lowered.split("weather")[-1].strip()
        if not city:
            city = "Tel Aviv"  # default city
        return get_weather(city)

    # Reminder setting
    elif "set reminder" in lowered:
        reminder_text, reminder_time = parse_reminder(lowered)
        if reminder_text and reminder_time:
            set_reminder(reminder_text, reminder_time)
            return P["reminder_set"] + reminder_time.strftime("%H:%M")
        else:
            return "Sorry, couldn't understand the reminder time."

    # Change personality
    elif "personality" in lowered:
        for mode in P["personalities"].keys():
            if mode in lowered:
                personality_var.set(mode)
                set_personality_mode()
                return P["personality_set"] + mode

    # Change language
    elif "language" in lowered:
        for lang in LANGUAGES.keys():
            if lang in lowered:
                language_var.set(lang)
                set_language()
                return P["language_set"]

    return None

def kill_process(proc_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and proc_name.lower() in proc.info['name'].lower():
            try:
                psutil.Process(proc.info['pid']).terminate()
            except Exception:
                pass

def confirm_and_shutdown():
    def shutdown():
        os.system("shutdown /s /t 1")

    # Ask confirmation GUI popup (run in main thread)
    def confirm():
        if messagebox.askyesno("Confirm Shutdown", "Are you sure you want to shut down the PC?"):
            threading.Thread(target=shutdown).start()

    root.after(0, confirm)

def change_volume(delta):
    # Windows only (using pycaw or ctypes)
    try:
        import ctypes
        devices = ctypes.windll.winmm.waveOutGetNumDevs()
        # Simple example, adjust master volume via Windows API
        from ctypes import POINTER, cast
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current_vol = volume.GetMasterVolumeLevelScalar()
        new_vol = min(max(0.0, current_vol + delta/100), 1.0)
        volume.SetMasterVolumeLevelScalar(new_vol, None)
    except Exception:
        pass

def mute_volume(mute):
    global volume_muted
    volume_muted = mute

def get_weather(city):
    try:
        # Use wttr.in free weather service (no API key required)
        url = f"http://wttr.in/{city}?format=3"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"Couldn't fetch weather for {city}."
    except Exception as e:
        logging.error(f"Weather fetch error: {e}")
        return "Sorry, I couldn't get the weather."

def parse_reminder(text):
    # Very simple parser example: "set reminder buy milk at 15:30"
    import re
    match = re.search(r"set reminder (.+) at (\d{1,2}:\d{2})", text)
    if match:
        reminder_text = match.group(1)
        time_str = match.group(2)
        now = datetime.now()
        try:
            reminder_time = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
            if reminder_time < now:
                reminder_time += timedelta(days=1)  # next day if time passed
            return reminder_text, reminder_time
        except:
            return None, None
    return None, None

def set_reminder(text, remind_time):
    reminders.append({"text": text, "time": remind_time})

def check_reminders():
    now = datetime.now()
    to_remove = []
    for r in reminders:
        if now >= r["time"]:
            notification.notify(
                title=P["reminder_alert"],
                message=r["text"],
                timeout=10
            )
            update_gui("Jarvis", f"Reminder: {r['text']}")
            speak(f"Reminder: {r['text']}")
            to_remove.append(r)
    for r in to_remove:
        reminders.remove(r)

# === Voice authentication ===
authorized = False

def is_authorized(command):
    global authorized
    if not VOICE_AUTH_ENABLED:
        return True
    if authorized:
        return True
    # Very simple phrase-based authentication
    if AUTHORIZED_USER_PHRASE in command.lower():
        authorized = True
        update_gui("System", "User authorized.")
        return True
    return False

# === Ask Ollama ===
def ask_ollama(prompt, history):
    convo = ""
    for h in history[-CHAT_HISTORY_LIMIT:]:
        convo += f"User: {h['user']}\nJarvis: {h['jarvis']}\n"
    convo += f"User: {prompt}\nJarvis:"

    # Add personality mode to prompt
    if personality_mode == "formal":
        convo = "Please respond formally.\n" + convo
    elif personality_mode == "humorous":
        convo = "Please respond with humor.\n" + convo
    # casual is default, no prefix

    data = {
        "model": OLLAMA_MODEL,
        "prompt": convo,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=data)
        response.raise_for_status()
        return response.json().get("response", "").strip() or "I didn't quite get that."
    except Exception as e:
        logging.error(f"Ollama API error: {e}")
        return P["ai_error"]

# === Wake Word Listener ===
def listen_for_wake_word():
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        update_gui("System", P["listening_wake"])
        while True:
            try:
                audio = recognizer.listen(source, timeout=10)
                transcript = recognizer.recognize_google(audio)
                update_gui("You", transcript)
                if TRIGGER_WORD in transcript.lower():
                    return
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                continue
            except Exception as e:
                logging.error(f"Wake word error: {e}")

# === Command Listener ===
def listen_for_command():
    with mic as source:
        update_gui("System", P["listening_command"])
        try:
            audio = recognizer.listen(source, timeout=10)
            command = recognizer.recognize_google(audio)
            update_gui("You", command)
            return command
        except sr.WaitTimeoutError:
            update_gui("System", P["command_timeout"])
        except sr.UnknownValueError:
            update_gui("System", P["unrecognized_speech"])
        except Exception as e:
            logging.error(f"Command error: {e}")
        return None

# === Assistant Core Loop ===
def assistant_loop():
    while True:
        update_gui("System", f"Say '{TRIGGER_WORD}' to wake me up...")
        listen_for_wake_word()
        update_gui("Jarvis", P["yes_sir"])
        speak(P["yes_sir"])
        last_interaction = time.time()

        while True:
            check_reminders()

            try:
                mobile_command = external_command_queue.get_nowait()
                if mobile_command:
                    handle_command(mobile_command)
                    last_interaction = time.time()
            except:
                pass

            command = listen_for_command()
            if command:
                handle_command(command)
                last_interaction = time.time()
            elif time.time() - last_interaction > CONVERSATION_TIMEOUT:
                update_gui("System", P["conversation_timeout"])
                break

# === Command Handler ===
def handle_command(command):
    response = try_system_command(command)
    if response:
        update_gui("Jarvis", response)
        speak(response)
        chat_history.append({"user": command, "jarvis": response})
    else:
        ai_reply = ask_ollama(command, chat_history)
        update_gui("Jarvis", ai_reply)
        speak(ai_reply)
        chat_history.append({"user": command, "jarvis": ai_reply})

def queue_external_command(command_text):
    external_command_queue.put(command_text)

# === Keyboard Hotkey Listener ===
def hotkey_listener():
    while True:
        keyboard.wait('ctrl+shift+j')
        update_gui("System", "Hotkey pressed, listening for command...")
        speak("Listening.")
        command = listen_for_command()
        if command:
            handle_command(command)

# === Start Threads ===
threading.Thread(target=assistant_loop, daemon=True).start()
threading.Thread(target=hotkey_listener, daemon=True).start()

# === GUI Mainloop and close handler ===
def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit Jarvis?"):
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# === Insert initial message ===
def init_message():
    update_gui("System", "Jarvis Initialized...\n")

def self_destruct():
    speak("Goodbye. Initiating self-destruct.")
    logging.info("Self destruct command received. Exiting.")
    os._exit(0)  # Forcefully exits the entire program


root.after(100, init_message)
root.mainloop()
