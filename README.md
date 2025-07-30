
# 🤖 Jarvis AI Assistant

Jarvis is a voice-activated desktop AI assistant built with Python. It combines speech recognition, text-to-speech, a GUI interface, Spotify controls, reminders, language switching, and personality modes. The assistant uses local AI (via Ollama) to respond intelligently to user queries.

---

## 🚀 Features

- 🎤 Wake word detection (`"Jarvis"`) and voice command listening
- 🧠 Local AI response using [Ollama](https://ollama.com/)
- 🗣️ Text-to-speech with `pyttsx3`
- 🖥️ Modern desktop GUI with `tkinter`
- 🎵 Full Spotify control (play, pause, next, shuffle, etc.)
- 🔒 Voice authentication (optional)
- 📅 Reminders with notifications
- 🌐 Google search & weather info (via `wttr.in`)
- 💬 Language switching (English / Spanish)
- 🎭 Personality modes (casual, formal, humorous)
- 📊 System status (CPU, RAM, battery)
- ⚙️ Open/close desktop apps (Notepad, Discord, Spotify, etc.)
- 🎧 Volume control (Windows only)
- 🧨 Self-destruct command (`"self destruct"` to close Jarvis)

---

## 🛠 Requirements

Install the dependencies with:

```bash
pip install -r requirements.txt
