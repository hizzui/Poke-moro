# Dib — Gamified Pomodoro & Task Tracker

![Dib Preview](https://github.com/user-attachments/assets/e2a32aea-788d-4d9b-a0dd-996316c4891d)

A Pomodoro focus timer and task tracker built entirely in **Python** with **Streamlit** and **SQLite**.

Each completed focus session rewards XP (`10 XP` per focus minute) toward leveling up one of three pixel-art animal companions (**Pássaro**, **Coruja**, or **Raposa**), while persisting session history and to-do items locally in `data/dib.db`.

---

## Project Structure

```text
Dib/
├── public/
│   ├── coruja.gif       # Owl companion pixel sprite
│   ├── passaro.gif      # Bird companion pixel sprite
│   └── raposa.gif       # Fox companion pixel sprite
├── app.py               # Streamlit Pomodoro UI, companion card, and task board
├── core.py              # Companion definitions and XP / level progression math
├── storage.py           # SQLite persistence layer (profile, sessions, tasks)
└── requirements.txt
```

---

## Running Locally

1. **Clone the repository and create a virtual environment:**
   ```bash
   git clone https://github.com/hizzui/Dib.git
   cd Dib
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the app:**
   ```bash
   streamlit run app.py
   ```
