# Poke-moro — Modern Anime Pokédex (Pure Python + Flet)

<img width="736" height="414" alt="Poke-moro Banner" src="public/pokemoro_banner.jpg" />

Reactive anime-inspired Pokédex web and desktop application built **100% in Pure Python** using **Flet** and **HTTPX** (`PokéAPI v2`). Designed around a zero-flicker, single-init component tree with granular in-place property updates (`control.update()`), in-memory caching, and automatic neighbor preloading.

## Architecture & Highlights

- **Zero-Flicker Reactive State:** Visual controls (`Container`, `Image`, `Text`, `ProgressBar`, and type badges) are instantiated only once on startup. Navigating between Pokémon mutates existing control properties in-place without calling `page.clean()` or rebuilding the DOM.
- **Async Caching & Neighbor Preloading:** Uses `httpx.AsyncClient` with an in-memory dictionary cache (`POKEMON_CACHE`) and background preloading of `#id - 1` and `#id + 1` for instant navigation.
- **Rotom-Phone Glassmorphism UI:** Centered single-page viewport with frosted glass blur (`ft.Blur`), dynamic radial background gradients that animate smoothly (`ft.Animation(400, "easeOut")`) based on the active Pokémon's primary type, and high-resolution official anime artwork (`official-artwork`).
- **Complete Navigation:** Lateral `<` and `>` buttons, keyboard arrow shortcuts (`Arrow Left` / `Arrow Right`), quick-pick anime favorites, instant search by name or `#ID` with inline error handling, and a Random Pokémon button (`1–1025`).

## Running Locally

```bash
git clone https://github.com/hizzui/Poke-moro.git
cd Poke-moro
pip install flet httpx
python main.py
```
