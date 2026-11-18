"""
Poké-moro — Sleek Rotom-OS & Pokémon Sleep Inspired Pomodoro Timer (100% Pure Python + Flet).
Designed following Apple Human Interface Guidelines:
- Single frameless glassmorphic vertical card (width=380, border_radius=32) with edge-to-edge top hero stage
- Dynamic atmospheric type gradient & giant translucent minimalist Pokéball watermark (opacity=0.07)
- High-presence animated Pokémon companion (145x145) with crisp pixel filtering and soft floor shadow
- Unified Segmented Control mode selector, frameless 68px protagonist timer, and 52px tactile action pill
- 4 mini-Pokéball cycle indicators, header micro-actions (⚡ instant evolution test & 🔍 modal search dialog)
- Zero-flicker single-init control tree with in-memory async PokéAPI caching

Install dependencies:
    pip install flet httpx
Run application:
    python main.py
"""

from __future__ import annotations

import asyncio
import os
import random
from typing import Any, Dict, List, Optional

import flet as ft
import httpx

# ---------------------------------------------------------------------------
# Flet Modern Compatibility Shims (Supports Flet 0.24.x through 0.27+)
# ---------------------------------------------------------------------------
if not hasattr(ft, "Colors") and hasattr(ft, "colors"):
    ft.Colors = ft.colors  # type: ignore[attr-defined]
if not hasattr(ft, "Icons") and hasattr(ft, "icons"):
    ft.Icons = ft.icons  # type: ignore[attr-defined]

Colors = ft.Colors
Icons = ft.Icons

# ---------------------------------------------------------------------------
# Constants, Atmospheric Type Palettes & Starter Lines
# ---------------------------------------------------------------------------
POKEAPI_BASE = "https://pokeapi.co/api/v2"
MAX_ANIMATED_ID = 649
CYCLES_PER_STREAK = 4

POMODORO_MODES: Dict[str, Dict[str, Any]] = {
    "focus":       {"label": "Foco 25m",  "seconds": 25 * 60, "override_hex": None},
    "short_break": {"label": "Pausa 5m",  "seconds": 5 * 60,  "override_hex": "#10B981"},
    "long_break":  {"label": "Longa 15m", "seconds": 15 * 60, "override_hex": "#38BDF8"},
}

TYPE_THEMES: Dict[str, Dict[str, str]] = {
    "fire":     {"label": "FIRE",     "accent": "#FF6B35", "grad_top": "#4D2212", "grad_mid": "#241313"},
    "water":    {"label": "WATER",    "accent": "#38BDF8", "grad_top": "#0F3156", "grad_mid": "#111D30"},
    "grass":    {"label": "GRASS",    "accent": "#34D399", "grad_top": "#0F3D2E", "grad_mid": "#112221"},
    "electric": {"label": "ELECTRIC", "accent": "#FACC15", "grad_top": "#4A3B0F", "grad_mid": "#221E12"},
    "ghost":    {"label": "GHOST",    "accent": "#C084FC", "grad_top": "#321852", "grad_mid": "#1B132B"},
    "psychic":  {"label": "PSYCHIC",  "accent": "#F472B6", "grad_top": "#4A153B", "grad_mid": "#231224"},
    "dragon":   {"label": "DRAGON",   "accent": "#818CF8", "grad_top": "#1E225A", "grad_mid": "#141730"},
    "dark":     {"label": "DARK",     "accent": "#94A3B8", "grad_top": "#1E293B", "grad_mid": "#131824"},
    "fairy":    {"label": "FAIRY",    "accent": "#F9A8D4", "grad_top": "#4A1936", "grad_mid": "#231322"},
    "fighting": {"label": "FIGHTING", "accent": "#FB923C", "grad_top": "#4A2012", "grad_mid": "#231514"},
    "steel":    {"label": "STEEL",    "accent": "#93C5FD", "grad_top": "#1E2D3D", "grad_mid": "#141B26"},
    "ice":      {"label": "ICE",      "accent": "#67E8F9", "grad_top": "#0E3A47", "grad_mid": "#11212B"},
    "poison":   {"label": "POISON",   "accent": "#C084FC", "grad_top": "#35164D", "grad_mid": "#1C1329"},
    "ground":   {"label": "GROUND",   "accent": "#FBBF24", "grad_top": "#422C0F", "grad_mid": "#201912"},
    "rock":     {"label": "ROCK",     "accent": "#F59E0B", "grad_top": "#3D2710", "grad_mid": "#1E1712"},
    "bug":      {"label": "BUG",      "accent": "#A3E635", "grad_top": "#283D11", "grad_mid": "#172013"},
    "flying":   {"label": "FLYING",   "accent": "#93C5FD", "grad_top": "#1B2C4E", "grad_mid": "#141B2C"},
    "normal":   {"label": "NORMAL",   "accent": "#CBD5E1", "grad_top": "#262F3F", "grad_mid": "#151A24"},
}

STARTER_LINES: List[List[int]] = [
    [4, 5, 6],       # Charmander -> Charmeleon -> Charizard
    [1, 2, 3],       # Bulbasaur -> Ivysaur -> Venusaur
    [7, 8, 9],       # Squirtle -> Wartortle -> Blastoise
    [172, 25, 26],   # Pichu -> Pikachu -> Raichu
    [92, 93, 94],    # Gastly -> Haunter -> Gengar
    [447, 448],      # Riolu -> Lucario
    [280, 281, 282], # Ralts -> Kirlia -> Gardevoir
    [133, 197],      # Eevee -> Umbreon
]

OFFLINE_FALLBACK_POKEMON: Dict[int, Dict[str, Any]] = {
    4:   {"id": 4,   "name": "Charmander", "types": ["fire"],            "chain": [4, 5, 6]},
    5:   {"id": 5,   "name": "Charmeleon", "types": ["fire"],            "chain": [4, 5, 6]},
    6:   {"id": 6,   "name": "Charizard",  "types": ["fire", "flying"],  "chain": [4, 5, 6]},
    1:   {"id": 1,   "name": "Bulbasaur",  "types": ["grass", "poison"], "chain": [1, 2, 3]},
    2:   {"id": 2,   "name": "Ivysaur",    "types": ["grass", "poison"], "chain": [1, 2, 3]},
    3:   {"id": 3,   "name": "Venusaur",   "types": ["grass", "poison"], "chain": [1, 2, 3]},
    7:   {"id": 7,   "name": "Squirtle",   "types": ["water"],           "chain": [7, 8, 9]},
    8:   {"id": 8,   "name": "Wartortle",  "types": ["water"],           "chain": [7, 8, 9]},
    9:   {"id": 9,   "name": "Blastoise",  "types": ["water"],           "chain": [7, 8, 9]},
    172: {"id": 172, "name": "Pichu",      "types": ["electric"],        "chain": [172, 25, 26]},
    25:  {"id": 25,  "name": "Pikachu",    "types": ["electric"],        "chain": [172, 25, 26]},
    26:  {"id": 26,  "name": "Raichu",     "types": ["electric"],        "chain": [172, 25, 26]},
    92:  {"id": 92,  "name": "Gastly",     "types": ["ghost", "poison"], "chain": [92, 93, 94]},
    93:  {"id": 93,  "name": "Haunter",    "types": ["ghost", "poison"], "chain": [92, 93, 94]},
    94:  {"id": 94,  "name": "Gengar",     "types": ["ghost", "poison"], "chain": [92, 93, 94]},
}

POKEMON_CACHE: Dict[str, Dict[str, Any]] = {}


def get_sprite_url(poke_id: int) -> str:
    if 1 <= poke_id <= MAX_ANIMATED_ID:
        return (
            "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
            f"sprites/pokemon/versions/generation-v/black-white/animated/{poke_id}.gif"
        )
    return (
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
        f"sprites/pokemon/other/official-artwork/{poke_id}.png"
    )


def build_offline_bundle(poke_id: int) -> Dict[str, Any]:
    base = OFFLINE_FALLBACK_POKEMON.get(
        poke_id,
        {"id": poke_id, "name": f"Pokémon #{poke_id}", "types": ["normal"], "chain": [poke_id]},
    )
    pid = base["id"]
    return {
        "id": pid,
        "code": f"#{pid:04d}",
        "name": base["name"],
        "types": base["types"],
        "primary_type": base["types"][0],
        "sprite_url": get_sprite_url(pid),
        "chain": base["chain"],
    }


def _extract_id(url: str) -> int:
    return int(url.rstrip("/").split("/")[-1])


def _parse_chain_ids(node: Dict[str, Any], acc: Optional[List[int]] = None) -> List[int]:
    if acc is None:
        acc = []
    if not node or "species" not in node:
        return acc
    acc.append(_extract_id(node["species"]["url"]))
    for child in node.get("evolves_to", []):
        _parse_chain_ids(child, acc)
    return acc


async def fetch_pokemon_with_evolution(client: httpx.AsyncClient, query: str | int) -> Dict[str, Any]:
    clean_key = str(query).strip().lower().lstrip("#")
    if clean_key.isdigit():
        clean_key = str(int(clean_key))

    if clean_key in POKEMON_CACHE:
        return POKEMON_CACHE[clean_key]

    try:
        resp = await client.get(f"{POKEAPI_BASE}/pokemon/{clean_key}", timeout=6.0)
        if resp.status_code != 200:
            raise ValueError(f"Pokémon '{query}' não encontrado.")

        raw = resp.json()
        poke_id: int = int(raw["id"])
        name: str = raw["name"].replace("-", " ").title()
        types: List[str] = [t["type"]["name"] for t in raw.get("types", [])] or ["normal"]

        animated_url = (
            raw.get("sprites", {})
            .get("versions", {})
            .get("generation-v", {})
            .get("black-white", {})
            .get("animated", {})
            .get("front_default")
        )
        official_url = (
            raw.get("sprites", {})
            .get("other", {})
            .get("official-artwork", {})
            .get("front_default")
        )
        sprite_url = animated_url or get_sprite_url(poke_id) or official_url

        chain_ids: List[int] = [poke_id]
        try:
            sp_url = raw.get("species", {}).get("url") or f"{POKEAPI_BASE}/pokemon-species/{poke_id}"
            sp_resp = await client.get(sp_url, timeout=5.0)
            if sp_resp.status_code == 200:
                evo_url = sp_resp.json().get("evolution_chain", {}).get("url")
                if evo_url:
                    evo_resp = await client.get(evo_url, timeout=5.0)
                    if evo_resp.status_code == 200:
                        parsed = _parse_chain_ids(evo_resp.json().get("chain", {}))
                        if parsed:
                            chain_ids = parsed
        except Exception:
            if poke_id in OFFLINE_FALLBACK_POKEMON:
                chain_ids = OFFLINE_FALLBACK_POKEMON[poke_id]["chain"]

        bundle = {
            "id": poke_id,
            "code": f"#{poke_id:04d}",
            "name": name,
            "types": types,
            "primary_type": types[0],
            "sprite_url": sprite_url,
            "chain": chain_ids,
        }
        POKEMON_CACHE[str(poke_id)] = bundle
        POKEMON_CACHE[raw["name"].lower()] = bundle
        return bundle

    except ValueError:
        raise
    except Exception:
        if clean_key.isdigit():
            fallback = build_offline_bundle(int(clean_key))
            POKEMON_CACHE[clean_key] = fallback
            return fallback
        for fb in OFFLINE_FALLBACK_POKEMON.values():
            if fb["name"].lower() == clean_key:
                fallback = build_offline_bundle(fb["id"])
                POKEMON_CACHE[clean_key] = fallback
                return fallback
        raise ValueError(f"Não foi possível carregar '{query}'.")


# ---------------------------------------------------------------------------
# Main Poké-moro Application (Sleek Rotom-OS / Pokémon Sleep Design)
# ---------------------------------------------------------------------------
async def main(page: ft.Page) -> None:
    page.title = "Poké-moro"
    page.padding = 16
    page.spacing = 0
    page.bgcolor = "#080B12"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    http_client = httpx.AsyncClient()

    init_bundle = build_offline_bundle(4)
    POKEMON_CACHE["4"] = init_bundle
    POKEMON_CACHE["charmander"] = init_bundle

    state: Dict[str, Any] = {
        "line_index": 0,
        "pokemon": init_bundle,
        "mode": "focus",
        "running": False,
        "total_seconds": POMODORO_MODES["focus"]["seconds"],
        "remaining_seconds": POMODORO_MODES["focus"]["seconds"],
        "cycles_completed": 0,
        "total_focus_completed": 0,
        "breath_up": False,
        "request_seq": 0,
    }

    # -----------------------------------------------------------------------
    # 1. Instantiate All Visual Controls ONCE (Zero Flickering Architecture)
    # -----------------------------------------------------------------------

    # Top Hero Micro-Header: Pokédex Code + Type Pill + Micro Action Icons (⚡ & 🔍)
    txt_code = ft.Text(
        value="#0004",
        size=13,
        weight=ft.FontWeight.W_800,
        color="#94A3B8",
    )

    type_pill = ft.Container(
        bgcolor="#26FF6B35",
        border=ft.border.all(1, "#66FF6B35"),
        border_radius=999,
        padding=ft.padding.symmetric(horizontal=10, vertical=3),
        content=ft.Text(
            value="FIRE",
            size=10,
            weight=ft.FontWeight.W_800,
            color="#FF6B35",
        ),
    )

    # High-Presence Pokémon Sprite (140x140) with Crisp Pixel Filtering & Floor Shadow
    filter_none = getattr(ft.FilterQuality, "NONE", None)
    img_pokemon = ft.Image(
        src=init_bundle["sprite_url"],
        width=136,
        height=136,
        fit=ft.ImageFit.CONTAIN,
        gapless_playback=True,
        filter_quality=filter_none,
    )

    sprite_holder = ft.Container(
        width=148,
        height=148,
        alignment=ft.alignment.center,
        scale=1.0,
        animate_scale=ft.Animation(800, ft.AnimationCurve.EASE_IN_OUT),
        content=img_pokemon,
    )

    floor_shadow = ft.Container(
        width=92,
        height=12,
        border_radius=50,
        bgcolor="#55000000",
    )

    txt_poke_name = ft.Text(
        value="Charmander",
        size=24,
        weight=ft.FontWeight.W_800,
        color="#F8FAFC",
        text_align=ft.TextAlign.CENTER,
    )

    txt_stage_subtitle = ft.Text(
        value="Estágio 1/3 • Evolui ao concluir o foco",
        size=11,
        weight=ft.FontWeight.W_500,
        color="#94A3B8",
        text_align=ft.TextAlign.CENTER,
    )

    evo_thin_bar = ft.ProgressBar(
        width=140,
        value=0.33,
        color="#FF6B35",
        bgcolor="#1F2937",
        bar_height=3,
        border_radius=2,
    )

    # Segmented Control Mode Pills (Foco 25m | Pausa 5m | Longa 15m)
    mode_pills: Dict[str, ft.Container] = {}

    # Protagonist Timer Display (68px frameless typography + 4px ultra-thin linear bar)
    txt_timer = ft.Text(
        value="25:00",
        size=68,
        weight=ft.FontWeight.W_800,
        color="#FFFFFF",
        text_align=ft.TextAlign.CENTER,
    )

    timer_thin_bar = ft.ProgressBar(
        value=1.0,
        color="#FF6B35",
        bgcolor="#1A2232",
        bar_height=4,
        border_radius=2,
    )

    # Primary Action Button (height=52, border_radius=18) + Subtle Circular Reset & Skip
    btn_primary_action = ft.Container(
        expand=True,
        height=52,
        bgcolor="#FF6B35",
        border_radius=18,
        alignment=ft.alignment.center,
        ink=True,
        shadow=ft.BoxShadow(
            blur_radius=20,
            color="#44FF6B35",
            offset=ft.Offset(0, 6),
        ),
        content=ft.Text(
            value="▶  Iniciar Foco",
            size=15,
            weight=ft.FontWeight.W_800,
            color="#080B12",
        ),
    )

    # 4 Mini-Pokéball Cycle Indicators
    mini_pokeballs: List[ft.Container] = []
    for _ in range(CYCLES_PER_STREAK):
        mini_pokeballs.append(
            ft.Container(
                width=20,
                height=20,
                border_radius=10,
                bgcolor="#161D2B",
                border=ft.border.all(1.8, "#2E3A4F"),
                alignment=ft.alignment.center,
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                content=ft.Container(
                    width=6,
                    height=6,
                    border_radius=3,
                    bgcolor="#2E3A4F",
                ),
            )
        )

    txt_sessions_count = ft.Text(
        value="0 / 4 Ciclos",
        size=12,
        weight=ft.FontWeight.W_600,
        color="#64748B",
    )

    # Search Modal Dialog Controls (Opened via 🔍 button in the header)
    modal_search_input = ft.TextField(
        hint_text="Nome ou #ID (ex: Pikachu, 25, Gengar, 448)...",
        hint_style=ft.TextStyle(color="#64748B", size=12),
        text_style=ft.TextStyle(color="#F8FAFC", size=13, weight=ft.FontWeight.W_600),
        bgcolor="#0B0F19",
        border_color="#263042",
        focused_border_color="#FF6B35",
        border_radius=12,
        height=42,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
        autofocus=True,
    )

    txt_modal_error = ft.Text(
        value="",
        size=11,
        weight=ft.FontWeight.W_600,
        color="#FCA5A5",
        visible=False,
    )

    # -----------------------------------------------------------------------
    # 2. Granular Theme & UI Synchronization (Zero Flickering)
    # -----------------------------------------------------------------------
    def get_active_accent() -> str:
        poke = state["pokemon"]
        p_type = poke["primary_type"]
        t_info = TYPE_THEMES.get(p_type, TYPE_THEMES["normal"])
        override = POMODORO_MODES[state["mode"]]["override_hex"]
        return override if override else t_info["accent"]

    def sync_card_ui(custom_subtitle: Optional[str] = None) -> None:
        poke = state["pokemon"]
        p_type = poke["primary_type"]
        t_info = TYPE_THEMES.get(p_type, TYPE_THEMES["normal"])
        type_accent = t_info["accent"]
        active_accent = get_active_accent()

        # 1. Dynamic Hero Stage Atmospheric Gradient
        if state["mode"] == "focus":
            grad_top = t_info["grad_top"]
            grad_mid = t_info["grad_mid"]
        elif state["mode"] == "short_break":
            grad_top = "#0D3B2E"
            grad_mid = "#102323"
        else:
            grad_top = "#0E2F4F"
            grad_mid = "#101E30"

        hero_stage.gradient = ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=[grad_top, grad_mid, "#101520"],
        )

        # Card ambient glow shadow
        sleek_card.shadow = ft.BoxShadow(
            spread_radius=0,
            blur_radius=50,
            color=f"#26{active_accent.lstrip('#')}",
            offset=ft.Offset(0, 18),
        )

        # 2. Header Code & Type Pill
        txt_code.value = poke["code"]
        type_pill.bgcolor = f"#22{type_accent.lstrip('#')}"
        type_pill.border = ft.border.all(1, f"#55{type_accent.lstrip('#')}")
        type_pill.content.value = t_info["label"]
        type_pill.content.color = type_accent

        # 3. Sprite & Evolution Progress
        if img_pokemon.src != poke["sprite_url"]:
            img_pokemon.src = poke["sprite_url"]

        txt_poke_name.value = poke["name"]

        chain: List[int] = poke.get("chain") or [poke["id"]]
        total_stages = len(chain)
        curr_idx = chain.index(poke["id"]) if poke["id"] in chain else 0
        stage_num = curr_idx + 1

        evo_thin_bar.value = round(stage_num / max(1, total_stages), 2)
        evo_thin_bar.color = type_accent

        if custom_subtitle:
            txt_stage_subtitle.value = custom_subtitle
        elif state["mode"] != "focus":
            txt_stage_subtitle.value = f"Descansando no Centro Pokémon • Estágio {stage_num}/{total_stages}"
        elif curr_idx + 1 < total_stages:
            txt_stage_subtitle.value = f"Estágio {stage_num}/{total_stages} • Evolui ao concluir o foco"
        else:
            txt_stage_subtitle.value = f"Estágio {stage_num}/{total_stages} • Forma Final Máxima"

        # 4. Segmented Control Active Pill
        for m_key, pill in mode_pills.items():
            is_sel = m_key == state["mode"]
            pill.bgcolor = "#1E2738" if is_sel else "#00000000"
            pill.border = ft.border.all(1, "#33FFFFFF") if is_sel else None
            pill.content.color = active_accent if is_sel else "#64748B"

        # 5. Timer Bar & Primary Action Button
        timer_thin_bar.color = active_accent
        if state["running"]:
            btn_primary_action.bgcolor = "#1E2738"
            btn_primary_action.shadow = None
            btn_primary_action.content.value = "⏸  Pausar"
            btn_primary_action.content.color = "#F8FAFC"
        else:
            label_action = "▶  Iniciar Foco" if state["mode"] == "focus" else "▶  Iniciar Pausa"
            btn_primary_action.bgcolor = active_accent
            btn_primary_action.shadow = ft.BoxShadow(
                blur_radius=20,
                color=f"#44{active_accent.lstrip('#')}",
                offset=ft.Offset(0, 6),
            )
            btn_primary_action.content.value = label_action
            btn_primary_action.content.color = "#080B12"

        # 6. 4 Mini-Pokéballs Indicator
        filled = state["cycles_completed"]
        for idx, ball in enumerate(mini_pokeballs):
            if idx < filled:
                ball.bgcolor = f"#28{active_accent.lstrip('#')}"
                ball.border = ft.border.all(1.8, active_accent)
                ball.content.bgcolor = active_accent
            else:
                ball.bgcolor = "#161D2B"
                ball.border = ft.border.all(1.8, "#2A3447")
                ball.content.bgcolor = "#2A3447"

        txt_sessions_count.value = (
            f"{filled} / {CYCLES_PER_STREAK} Ciclos"
            if state["total_focus_completed"] == 0
            else f"{filled} / {CYCLES_PER_STREAK} Ciclos • {state['total_focus_completed']} Total"
        )

    def sync_clock_only() -> None:
        m, s = divmod(max(0, state["remaining_seconds"]), 60)
        txt_timer.value = f"{m:02d}:{s:02d}"
        total = max(1, state["total_seconds"])
        timer_thin_bar.value = max(0.0, min(1.0, state["remaining_seconds"] / total))

    # -----------------------------------------------------------------------
    # 3. Async PokéAPI Partner Loader & Progressive Evolution
    # -----------------------------------------------------------------------
    async def load_pokemon(
        query_or_id: str | int,
        custom_subtitle: Optional[str] = None,
        pulse: bool = False,
    ) -> bool:
        req_id = state["request_seq"] + 1
        state["request_seq"] = req_id

        try:
            bundle = await fetch_pokemon_with_evolution(http_client, query_or_id)
        except Exception as exc:
            if req_id != state["request_seq"]:
                return False
            txt_modal_error.value = str(exc)
            txt_modal_error.visible = True
            try:
                txt_modal_error.update()
            except Exception:
                pass
            return False

        if req_id != state["request_seq"]:
            return False

        state["pokemon"] = bundle
        if custom_subtitle and custom_subtitle.startswith("__EVOLVED_FROM__:"):
            prev_n = custom_subtitle.split(":", 1)[1]
            custom_subtitle = f"✨ {prev_n} evoluiu para {bundle['name']}!"
        elif custom_subtitle == "__RESET_STAGE__":
            custom_subtitle = f"Estágio 1/{len(bundle.get('chain', [1]))} • Ciclo evolutivo reiniciado"

        sync_card_ui(custom_subtitle=custom_subtitle)

        if pulse:
            sprite_holder.scale = 1.24
            sleek_card.update()
            await asyncio.sleep(0.32)
            sprite_holder.scale = 1.0

        sleek_card.update()
        return True

    async def trigger_evolution() -> None:
        poke = state["pokemon"]
        chain: List[int] = poke.get("chain") or [poke["id"]]
        if len(chain) <= 1:
            txt_stage_subtitle.value = f"{poke['name']} possui estágio único."
            txt_stage_subtitle.update()
            return

        curr_idx = chain.index(poke["id"]) if poke["id"] in chain else 0
        next_idx = (curr_idx + 1) % len(chain)
        next_id = chain[next_idx]
        prev_name = poke["name"]

        await load_pokemon(
            next_id,
            custom_subtitle="__EVOLVED_FROM__:" + prev_name if next_idx > curr_idx else "__RESET_STAGE__",
            pulse=True,
        )

    # -----------------------------------------------------------------------
    # 4. Background Loops: 1s Pomodoro Timer & Idle Sprite Float Motion
    # -----------------------------------------------------------------------
    async def handle_session_finished() -> None:
        state["running"] = False
        if state["mode"] == "focus":
            state["total_focus_completed"] += 1
            state["cycles_completed"] += 1

            poke = state["pokemon"]
            chain: List[int] = poke.get("chain") or [poke["id"]]
            curr_idx = chain.index(poke["id"]) if poke["id"] in chain else 0
            can_evolve = curr_idx + 1 < len(chain)

            if state["cycles_completed"] >= CYCLES_PER_STREAK:
                state["cycles_completed"] = 0
                state["mode"] = "long_break"
            else:
                state["mode"] = "short_break"

            state["total_seconds"] = POMODORO_MODES[state["mode"]]["seconds"]
            state["remaining_seconds"] = state["total_seconds"]
            sync_clock_only()

            if can_evolve:
                await trigger_evolution()
                return
        else:
            state["mode"] = "focus"
            state["total_seconds"] = POMODORO_MODES["focus"]["seconds"]
            state["remaining_seconds"] = state["total_seconds"]
            sync_clock_only()

        sync_card_ui()
        sleek_card.update()

    async def timer_background_task() -> None:
        while True:
            await asyncio.sleep(1)
            state["breath_up"] = not state["breath_up"]
            sprite_holder.scale = 1.05 if state["breath_up"] else 0.98
            try:
                sprite_holder.update()
            except Exception:
                pass

            if not state["running"]:
                continue

            state["remaining_seconds"] = max(0, state["remaining_seconds"] - 1)
            sync_clock_only()

            if state["remaining_seconds"] <= 0:
                await handle_session_finished()
            else:
                txt_timer.update()
                timer_thin_bar.update()

    # -----------------------------------------------------------------------
    # 5. User Interaction Callbacks & Clean Search Modal
    # -----------------------------------------------------------------------
    async def on_switch_mode(new_mode: str) -> None:
        state["running"] = False
        state["mode"] = new_mode
        state["total_seconds"] = POMODORO_MODES[new_mode]["seconds"]
        state["remaining_seconds"] = state["total_seconds"]
        sync_clock_only()
        sync_card_ui()
        sleek_card.update()

    async def on_primary_action(_: ft.ControlEvent) -> None:
        state["running"] = not state["running"]
        sync_card_ui()
        btn_primary_action.update()
        txt_stage_subtitle.update()

    async def on_reset(_: ft.ControlEvent) -> None:
        state["running"] = False
        state["remaining_seconds"] = state["total_seconds"]
        sync_clock_only()
        sync_card_ui()
        txt_timer.update()
        timer_thin_bar.update()
        btn_primary_action.update()
        txt_stage_subtitle.update()

    async def on_skip(_: ft.ControlEvent) -> None:
        await handle_session_finished()

    async def on_prev_line(_: ft.ControlEvent) -> None:
        state["line_index"] = (state["line_index"] - 1) % len(STARTER_LINES)
        base_id = STARTER_LINES[state["line_index"]][0]
        await load_pokemon(base_id)

    async def on_next_line(_: ft.ControlEvent) -> None:
        state["line_index"] = (state["line_index"] + 1) % len(STARTER_LINES)
        base_id = STARTER_LINES[state["line_index"]][0]
        await load_pokemon(base_id)

    async def on_bolt_evolve(_: ft.ControlEvent) -> None:
        await trigger_evolution()

    # Search Modal Dialog (ft.AlertDialog)
    def close_search_modal(_: Optional[ft.ControlEvent] = None) -> None:
        search_dialog.open = False
        page.update()

    async def submit_modal_search(_: Optional[ft.ControlEvent] = None) -> None:
        q = (modal_search_input.value or "").strip()
        if not q:
            return
        txt_modal_error.visible = False
        ok = await load_pokemon(q)
        if ok:
            modal_search_input.value = ""
            close_search_modal()

    async def random_from_modal(_: ft.ControlEvent) -> None:
        txt_modal_error.visible = False
        ok = await load_pokemon(random.randint(1, MAX_ANIMATED_ID))
        if ok:
            modal_search_input.value = ""
            close_search_modal()

    modal_search_input.on_submit = submit_modal_search

    search_dialog = ft.AlertDialog(
        modal=False,
        bgcolor="#121826",
        shape=ft.RoundedRectangleBorder(radius=22),
        title=ft.Text("Escolher Companheiro", size=17, weight=ft.FontWeight.W_800, color="#F8FAFC"),
        content=ft.Container(
            width=310,
            content=ft.Column(
                spacing=10,
                tight=True,
                controls=[
                    modal_search_input,
                    txt_modal_error,
                    ft.Text(
                        "Dica: Busque qualquer Pokémon de #1 a #1025 ou sorteie um aleatório.",
                        size=11,
                        color="#64748B",
                    ),
                ],
            ),
        ),
        actions=[
            ft.TextButton(
                "Aleatório",
                icon=Icons.SHUFFLE,
                style=ft.ButtonStyle(color="#FACC15"),
                on_click=random_from_modal,
            ),
            ft.TextButton(
                "Cancelar",
                style=ft.ButtonStyle(color="#94A3B8"),
                on_click=close_search_modal,
            ),
            ft.ElevatedButton(
                "Selecionar",
                bgcolor="#FF6B35",
                color="#080B12",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=submit_modal_search,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(search_dialog)

    def open_search_modal(_: ft.ControlEvent) -> None:
        txt_modal_error.visible = False
        search_dialog.open = True
        page.update()

    btn_primary_action.on_click = on_primary_action

    # -----------------------------------------------------------------------
    # 6. Assemble Single Sleek Vertical Card (Width=380, BorderRadius=32)
    # -----------------------------------------------------------------------

    # Top Micro Action Buttons (⚡ Instant Evolution Test & 🔍 Search Modal)
    btn_micro_evolve = ft.Container(
        width=32,
        height=32,
        border_radius=16,
        bgcolor="#1AFFFFFF",
        alignment=ft.alignment.center,
        ink=True,
        tooltip="Testar Evolução (⚡)",
        on_click=on_bolt_evolve,
        content=ft.Icon(Icons.BOLT, color="#FACC15", size=17),
    )

    btn_micro_search = ft.Container(
        width=32,
        height=32,
        border_radius=16,
        bgcolor="#1AFFFFFF",
        alignment=ft.alignment.center,
        ink=True,
        tooltip="Buscar ou Sortear Pokémon (🔍)",
        on_click=open_search_modal,
        content=ft.Icon(Icons.SEARCH, color="#E2E8F0", size=16),
    )

    # Discreet Translucent `<` and `>` Arrows on Hero Stage Edges
    btn_hero_prev = ft.Container(
        width=34,
        height=34,
        border_radius=17,
        bgcolor="#14FFFFFF",
        alignment=ft.alignment.center,
        ink=True,
        tooltip="Companheiro Anterior",
        on_click=on_prev_line,
        content=ft.Icon(Icons.CHEVRON_LEFT, color="#CBD5E1", size=20),
    )

    btn_hero_next = ft.Container(
        width=34,
        height=34,
        border_radius=17,
        bgcolor="#14FFFFFF",
        alignment=ft.alignment.center,
        ink=True,
        tooltip="Próximo Companheiro",
        on_click=on_next_line,
        content=ft.Icon(Icons.CHEVRON_RIGHT, color="#CBD5E1", size=20),
    )

    # Giant Translucent Minimalist Pokéball Watermark (opacity ~0.07 via #11FFFFFF)
    pokeball_watermark = ft.Stack(
        width=200,
        height=200,
        alignment=ft.alignment.center,
        controls=[
            ft.Container(
                width=190,
                height=190,
                border_radius=95,
                border=ft.border.all(14, "#10FFFFFF"),
            ),
            ft.Container(
                width=190,
                height=10,
                bgcolor="#10FFFFFF",
            ),
            ft.Container(
                width=52,
                height=52,
                border_radius=26,
                bgcolor="#151821",
                border=ft.border.all(11, "#12FFFFFF"),
            ),
        ],
    )

    # Top Hero Stage Container (Edge-to-Edge Atmospheric Type Gradient)
    hero_stage = ft.Container(
        padding=ft.padding.only(left=20, right=20, top=18, bottom=14),
        animate=ft.Animation(450, ft.AnimationCurve.EASE_OUT),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#4D2212", "#241313", "#101520"],
        ),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            tight=True,
            controls=[
                # Single flat Header Row (Uses expanding spacer instead of nested Rows!)
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        txt_code,
                        type_pill,
                        ft.Container(expand=True),
                        btn_micro_evolve,
                        btn_micro_search,
                    ],
                ),
                # Hero Centerpiece: `<` + Pokéball Watermark & Floating Pokémon + `>`
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        btn_hero_prev,
                        ft.Stack(
                            width=210,
                            height=185,
                            alignment=ft.alignment.center,
                            controls=[
                                pokeball_watermark,
                                ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=0,
                                    controls=[
                                        sprite_holder,
                                        floor_shadow,
                                    ],
                                ),
                            ],
                        ),
                        btn_hero_next,
                    ],
                ),
                # Pokémon Name + Integrated Evolution Stage Bar (Clickable to test evolution)
                txt_poke_name,
                ft.Container(
                    on_click=on_bolt_evolve,
                    ink=True,
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=10, vertical=2),
                    tooltip="Clique para testar a evolução",
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        tight=True,
                        controls=[
                            txt_stage_subtitle,
                            evo_thin_bar,
                        ],
                    ),
                ),
            ],
        ),
    )

    # Unified Segmented Control Bar for Timer Modes
    for m_key, m_cfg in POMODORO_MODES.items():
        is_sel = m_key == "focus"
        pill = ft.Container(
            expand=True,
            height=34,
            bgcolor="#1E2738" if is_sel else "#00000000",
            border=ft.border.all(1, "#33FFFFFF") if is_sel else None,
            border_radius=10,
            alignment=ft.alignment.center,
            ink=True,
            on_click=lambda _, mk=m_key: page.run_task(on_switch_mode, mk),
            content=ft.Text(
                value=m_cfg["label"],
                size=11,
                weight=ft.FontWeight.W_700,
                color="#FF6B35" if is_sel else "#64748B",
            ),
        )
        mode_pills[m_key] = pill

    segmented_control = ft.Container(
        bgcolor="#0A0E17",
        border=ft.border.all(1, "#18FFFFFF"),
        border_radius=14,
        padding=ft.padding.all(4),
        content=ft.Row(
            spacing=4,
            controls=list(mode_pills.values()),
        ),
    )

    # Subtle Circular Secondary Action Buttons (Reset & Skip)
    btn_circle_reset = ft.Container(
        width=50,
        height=50,
        border_radius=16,
        bgcolor="#171E2E",
        border=ft.border.all(1, "#242F46"),
        alignment=ft.alignment.center,
        ink=True,
        tooltip="Resetar Cronômetro",
        on_click=on_reset,
        content=ft.Icon(Icons.REFRESH, color="#CBD5E1", size=20),
    )

    btn_circle_skip = ft.Container(
        width=50,
        height=50,
        border_radius=16,
        bgcolor="#171E2E",
        border=ft.border.all(1, "#242F46"),
        alignment=ft.alignment.center,
        ink=True,
        tooltip="Concluir / Pular Ciclo",
        on_click=on_skip,
        content=ft.Icon(Icons.SKIP_NEXT, color="#CBD5E1", size=22),
    )

    # Bottom Timer Surface (Frameless Clock, Ultra-thin bar, Tactile Controls & Mini-Pokéballs)
    timer_surface = ft.Container(
        padding=ft.padding.only(left=24, right=24, top=6, bottom=22),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            tight=True,
            controls=[
                segmented_control,
                # Protagonist Clock directly on card background
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                    tight=True,
                    controls=[
                        txt_timer,
                        timer_thin_bar,
                    ],
                ),
                # Action Controls Row
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        btn_circle_reset,
                        btn_primary_action,
                        btn_circle_skip,
                    ],
                ),
                # Base Footer: 4 Mini-Pokéballs + Cycle Counter (Single flat Row!)
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        *mini_pokeballs,
                        ft.Container(expand=True),
                        txt_sessions_count,
                    ],
                ),
            ],
        ),
    )

    # Single Sleek Vertical Card (Width=380, BorderRadius=32, Rotom-OS Glassmorphism)
    sleek_card = ft.Container(
        width=380,
        bgcolor="#101520",
        border=ft.border.all(1, "#22FFFFFF"),
        border_radius=32,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        animate=ft.Animation(450, ft.AnimationCurve.EASE_OUT),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=50,
            color="#26FF6B35",
            offset=ft.Offset(0, 18),
        ),
        content=ft.Column(
            spacing=0,
            tight=True,
            controls=[
                hero_stage,
                timer_surface,
            ],
        ),
    )

    # Render immediately with offline defaults so the screen never stalls or flashes grey
    sync_card_ui()
    page.add(sleek_card)

    # Start background tasks via Flet's modern page.run_task()
    page.run_task(timer_background_task)
    page.run_task(load_pokemon, 4)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8501"))
    web_view = getattr(ft.AppView, "FLET_APP_WEB", ft.AppView.WEB_BROWSER)
    ft.app(target=main, view=web_view, port=port)
