# Poke-moro — Pokémon Pomodoro & Task Tracker

<img width="736" height="414" alt="Poke-moro Banner" src="public/pokemoro_banner.jpg" />

Gamified Pomodoro timer and task tracker built with **Python**, **Streamlit**, and **SQLite**, featuring animated Gen-V pixel-art Pokémon partners that level up and evolve as you complete focus sessions. Fully responsive across desktop and mobile viewports.

## Features

- **5 Partner Evolution Lines (15 Animated Sprites):**
  - **Charmander** (Lv. 1) → **Charmeleon** (Lv. 5) → **Charizard** (Lv. 10)
  - **Bulbasaur** (Lv. 1) → **Ivysaur** (Lv. 5) → **Venusaur** (Lv. 10)
  - **Squirtle** (Lv. 1) → **Wartortle** (Lv. 5) → **Blastoise** (Lv. 10)
  - **Pichu** (Lv. 1) → **Pikachu** (Lv. 5) → **Raichu** (Lv. 10)
  - **Gastly** (Lv. 1) → **Haunter** (Lv. 5) → **Gengar** (Lv. 10)
- **EXP & Evolution System:** Earn **10 EXP per focus minute** completed (`100 EXP` per level) and watch your partner evolve automatically in the Pokédex card.
- **Mobile-Responsive UI:** Fluid `clamp()` timer typography, 2×2 touch-friendly control grid, 3-column compact stats bar, and an inline settings drawer so mobile users can switch Pokémon or adjust timer durations without opening a hidden sidebar.
- **Local SQLite Persistence:** All trainer stats, active evolution line, and quest tasks are stored locally in `data/dib.db`.

## Running Locally

```bash
git clone https://github.com/hizzui/Poke-moro.git
cd Poke-moro
pip install -r requirements.txt
streamlit run app.py
```
