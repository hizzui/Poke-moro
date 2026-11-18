"""
Poke-moro — Modern Anime Pokédex & Focus Timer built 100% in Pure Python with Flet & HTTPX.
Features zero-flicker granular state updates, in-memory async caching, neighbor preloading,
Glassmorphism Rotom-Dex UI, dynamic type-based radial gradients, and an integrated Pomodoro timer.
"""

from __future__ import annotations

import asyncio
import os
import random
from typing import Any, Dict, List

import flet as ft
import httpx

# ---------------------------------------------------------------------------
# Constants & Anime Type Color Themes
# ---------------------------------------------------------------------------
POKEAPI_BASE = "https://pokeapi.co/api/v2"
MAX_POKEMON_ID = 1025

Icons = getattr(ft, "Icons", getattr(ft, "icons", None))

TYPE_PALETTE: Dict[str, Dict[str, str]] = {
    "fire":     {"label": "FIRE",     "primary": "#FF5722", "secondary": "#B91C1C", "bg_dark": "#1F0909"},
    "water":    {"label": "WATER",    "primary": "#00B4D8", "secondary": "#0369A1", "bg_dark": "#071521"},
    "grass":    {"label": "GRASS",    "primary": "#10B981", "secondary": "#047857", "bg_dark": "#071C15"},
    "electric": {"label": "ELECTRIC", "primary": "#FACC15", "secondary": "#CA8A04", "bg_dark": "#1D1907"},
    "ghost":    {"label": "GHOST",    "primary": "#A855F7", "secondary": "#6B21A8", "bg_dark": "#140921"},
    "psychic":  {"label": "PSYCHIC",  "primary": "#EC4899", "secondary": "#BE185D", "bg_dark": "#1F0916"},
    "dragon":   {"label": "DRAGON",   "primary": "#6366F1", "secondary": "#3730A3", "bg_dark": "#0B0D24"},
    "dark":     {"label": "DARK",     "primary": "#94A3B8", "secondary": "#334155", "bg_dark": "#0B0F17"},
    "fairy":    {"label": "FAIRY",    "primary": "#F472B6", "secondary": "#DB2777", "bg_dark": "#1F0B18"},
    "fighting": {"label": "FIGHTING", "primary": "#F97316", "secondary": "#C2410C", "bg_dark": "#1F0E07"},
    "steel":    {"label": "STEEL",    "primary": "#38BDF8", "secondary": "#475569", "bg_dark": "#0D1520"},
    "ice":      {"label": "ICE",      "primary": "#67E8F9", "secondary": "#0891B2", "bg_dark": "#071A21"},
    "poison":   {"label": "POISON",   "primary": "#C084FC", "secondary": "#7E22CE", "bg_dark": "#170924"},
    "ground":   {"label": "GROUND",   "primary": "#FBBF24", "secondary": "#B45309", "bg_dark": "#1C1408"},
    "rock":     {"label": "ROCK",     "primary": "#D97706", "secondary": "#78350F", "bg_dark": "#1A1208"},
    "bug":      {"label": "BUG",      "primary": "#84CC16", "secondary": "#4D7C0F", "bg_dark": "#111A08"},
    "flying":   {"label": "FLYING",   "primary": "#818CF8", "secondary": "#4F46E5", "bg_dark": "#0D1024"},
    "normal":   {"label": "NORMAL",   "primary": "#94A3B8", "secondary": "#475569", "bg_dark": "#0F141C"},
}

STAT_CONFIG: List[Dict[str, str]] = [
    {"key": "hp",              "label": "HP",      "color": "#EF4444"},
    {"key": "attack",          "label": "Attack",  "color": "#F97316"},
    {"key": "defense",         "label": "Defense", "color": "#EAB308"},
    {"key": "special-attack",  "label": "Sp. Atk", "color": "#3B82F6"},
    {"key": "special-defense", "label": "Sp. Def", "color": "#10B981"},
    {"key": "speed",           "label": "Speed",   "color": "#EC4899"},
]

# In-memory cache to make visited Pokémon transitions instantaneous (0ms network wait)
POKEMON_CACHE: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Async PokéAPI Service Layer
# ---------------------------------------------------------------------------
async def fetch_pokemon_data(client: httpx.AsyncClient, query: str | int) -> Dict[str, Any]:
    """Fetch and normalize Pokémon data from PokéAPI with in-memory caching."""
    clean_key = str(query).strip().lower().lstrip("#")
    if clean_key.isdigit():
        clean_key = str(int(clean_key))

    if clean_key in POKEMON_CACHE:
        return POKEMON_CACHE[clean_key]

    resp = await client.get(f"{POKEAPI_BASE}/pokemon/{clean_key}", timeout=8.0)
    if resp.status_code != 200:
        raise ValueError(f"Pokémon '{query}' not found.")

    raw = resp.json()
    poke_id: int = raw["id"]
    name: str = raw["name"].replace("-", " ").title()
    types: List[str] = [t["type"]["name"] for t in raw.get("types", [])]
    primary_type: str = types[0] if types else "normal"

    artwork_url: str = (
        raw.get("sprites", {})
        .get("other", {})
        .get("official-artwork", {})
        .get("front_default")
        or f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke_id}.png"
    )

    stats_map: Dict[str, int] = {
        s["stat"]["name"]: int(s["base_stat"]) for s in raw.get("stats", [])
    }
    total_stats: int = sum(stats_map.values())

    abilities: List[str] = [
        a["ability"]["name"].replace("-", " ").title()
        for a in raw.get("abilities", [])[:3]
    ]

    height_m: float = round(raw.get("height", 0) / 10.0, 1)
    weight_kg: float = round(raw.get("weight", 0) / 10.0, 1)
    base_exp: int = raw.get("base_experience") or 0

    data = {
        "id": poke_id,
        "code": f"#{poke_id:04d}",
        "name": name,
        "types": types,
        "primary_type": primary_type,
        "artwork_url": artwork_url,
        "stats": stats_map,
        "total_stats": total_stats,
        "abilities": ", ".join(abilities) if abilities else "Unknown",
        "height": f"{height_m} m",
        "weight": f"{weight_kg} kg",
        "base_exp": str(base_exp),
    }

    POKEMON_CACHE[str(poke_id)] = data
    POKEMON_CACHE[raw["name"].lower()] = data
    return data


# ---------------------------------------------------------------------------
# Main Reactive Flet Application (Single-Init DOM, Zero Flickering)
# ---------------------------------------------------------------------------
async def main(page: ft.Page) -> None:
    page.title = "Poke-moro — Rotom Pokédex & Focus Hub"
    page.padding = 0
    page.spacing = 0
    page.bgcolor = "#070A10"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    http_client = httpx.AsyncClient()
    state: Dict[str, Any] = {
        "current_id": 25,
        "request_seq": 0,
        "timer_running": False,
        "timer_seconds": 25 * 60,
        "trainer_xp": 0,
    }

    # -----------------------------------------------------------------------
    # 1. Instantiate Visual Controls ONCE (Never destroyed or recreated)
    # -----------------------------------------------------------------------
    search_input = ft.TextField(
        hint_text="Search Pokémon name or #ID (e.g. Charizard, 6, Gengar)...",
        hint_style=ft.TextStyle(color="#64748B", size=13),
        text_style=ft.TextStyle(color="#F8FAFC", size=13, weight=ft.FontWeight.W_500),
        bgcolor="#99090D16",
        border_color="#26FFFFFF",
        focused_border_color="#FF5722",
        border_radius=14,
        height=42,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=8),
        expand=True,
    )

    loading_ring = ft.ProgressRing(
        width=18,
        height=18,
        stroke_width=2.2,
        color="#FACC15",
        visible=False,
    )

    error_banner = ft.Container(
        visible=False,
        bgcolor="#33EF4444",
        border=ft.border.all(1, "#66EF4444"),
        border_radius=10,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        content=ft.Text(
            value="",
            color="#FCA5A5",
            size=12,
            weight=ft.FontWeight.W_600,
        ),
    )

    # Pomodoro Timer Controls (Updated granularly via txt_timer.update())
    txt_timer = ft.Text(
        value="25:00",
        size=16,
        weight=ft.FontWeight.W_900,
        color="#FFFFFF",
    )
    txt_trainer_xp = ft.Text(
        value="0 EXP",
        size=11,
        weight=ft.FontWeight.W_800,
        color="#FACC15",
    )

    txt_watermark = ft.Text(
        value="#0025",
        size=84,
        weight=ft.FontWeight.W_900,
        color="#12FFFFFF",
        text_align=ft.TextAlign.CENTER,
    )

    img_pokemon = ft.Image(
        src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png",
        width=190,
        height=190,
        fit=ft.ImageFit.CONTAIN,
        gapless_playback=True,
    )

    img_wrapper = ft.Container(
        content=img_pokemon,
        opacity=1.0,
        animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        alignment=ft.alignment.center,
    )

    hero_glow_orb = ft.Container(
        width=160,
        height=160,
        border_radius=100,
        bgcolor="#33FACC15",
        animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
    )

    txt_code_pill = ft.Text(
        value="#0025 • ROTOM DEX",
        size=12,
        weight=ft.FontWeight.W_800,
        color="#FACC15",
    )

    txt_name = ft.Text(
        value="Pikachu",
        size=28,
        weight=ft.FontWeight.W_900,
        color="#FFFFFF",
        text_align=ft.TextAlign.CENTER,
    )

    badges_row = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
        controls=[],
    )

    txt_height_val = ft.Text("0.4 m", size=14, weight=ft.FontWeight.W_800, color="#F8FAFC")
    txt_weight_val = ft.Text("6.0 kg", size=14, weight=ft.FontWeight.W_800, color="#F8FAFC")
    txt_exp_val = ft.Text("112", size=14, weight=ft.FontWeight.W_800, color="#F8FAFC")
    txt_abilities_val = ft.Text(
        "Static, Lightning Rod",
        size=12,
        weight=ft.FontWeight.W_700,
        color="#E2E8F0",
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS,
    )

    stat_value_texts: Dict[str, ft.Text] = {}
    stat_progress_bars: Dict[str, ft.ProgressBar] = {}
    stat_rows: List[ft.Control] = []

    for sc in STAT_CONFIG:
        s_key = sc["key"]
        val_txt = ft.Text(
            value="50",
            size=12,
            weight=ft.FontWeight.W_800,
            color="#FFFFFF",
            width=32,
            text_align=ft.TextAlign.RIGHT,
        )
        p_bar = ft.ProgressBar(
            value=0.35,
            color=sc["color"],
            bgcolor="#1E293B",
            bar_height=7,
            border_radius=6,
            expand=True,
        )
        stat_value_texts[s_key] = val_txt
        stat_progress_bars[s_key] = p_bar
        stat_rows.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Text(
                        sc["label"],
                        size=12,
                        weight=ft.FontWeight.W_700,
                        color="#94A3B8",
                        width=58,
                    ),
                    val_txt,
                    p_bar,
                ],
            )
        )

    txt_total_stats = ft.Text(
        value="BASE STAT TOTAL: 320",
        size=12,
        weight=ft.FontWeight.W_900,
        color="#FACC15",
    )

    # -----------------------------------------------------------------------
    # 2. Granular Update Routine (Mutates properties in-place, zero flicker)
    # -----------------------------------------------------------------------
    async def preload_neighbors(center_id: int) -> None:
        prev_id = center_id - 1 if center_id > 1 else MAX_POKEMON_ID
        next_id = center_id + 1 if center_id < MAX_POKEMON_ID else 1
        for neighbor in (prev_id, next_id):
            if str(neighbor) not in POKEMON_CACHE:
                try:
                    await fetch_pokemon_data(http_client, neighbor)
                except Exception:
                    pass

    async def load_pokemon(query_or_id: str | int) -> None:
        req_id = state["request_seq"] + 1
        state["request_seq"] = req_id

        clean_key = str(query_or_id).strip().lower().lstrip("#")
        is_cached = clean_key in POKEMON_CACHE

        if not is_cached:
            loading_ring.visible = True
            img_wrapper.opacity = 0.4
            loading_ring.update()
            img_wrapper.update()

        try:
            data = await fetch_pokemon_data(http_client, query_or_id)
        except Exception as exc:
            if req_id != state["request_seq"]:
                return
            loading_ring.visible = False
            img_wrapper.opacity = 1.0
            error_banner.content.value = str(exc)
            error_banner.visible = True
            loading_ring.update()
            img_wrapper.update()
            error_banner.update()
            return

        if req_id != state["request_seq"]:
            return

        state["current_id"] = data["id"]
        theme = TYPE_PALETTE.get(data["primary_type"], TYPE_PALETTE["normal"])
        primary_hex = theme["primary"]

        error_banner.visible = False
        loading_ring.visible = False

        bg_wrapper.gradient = ft.RadialGradient(
            center=ft.Alignment(0, -0.35),
            radius=1.15,
            colors=[
                f"#44{primary_hex.lstrip('#')}",
                theme["bg_dark"],
                "#06080E",
            ],
        )
        glass_card.border = ft.border.all(1.5, f"#40{primary_hex.lstrip('#')}")
        glass_card.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=45,
            color=f"#33{primary_hex.lstrip('#')}",
            offset=ft.Offset(0, 14),
        )
        hero_glow_orb.bgcolor = f"#38{primary_hex.lstrip('#')}"
        search_input.focused_border_color = primary_hex

        txt_watermark.value = data["code"]
        txt_code_pill.value = f"{data['code']} • ROTOM DEX"
        txt_code_pill.color = primary_hex
        txt_trainer_xp.color = primary_hex
        txt_name.value = data["name"]
        img_pokemon.src = data["artwork_url"]
        img_wrapper.opacity = 1.0

        new_badges: List[ft.Control] = []
        for t_name in data["types"]:
            t_info = TYPE_PALETTE.get(t_name, TYPE_PALETTE["normal"])
            new_badges.append(
                ft.Container(
                    bgcolor=t_info["primary"],
                    border_radius=20,
                    padding=ft.padding.symmetric(horizontal=14, vertical=5),
                    content=ft.Text(
                        value=t_info["label"],
                        size=11,
                        weight=ft.FontWeight.W_900,
                        color="#090D16",
                    ),
                )
            )
        badges_row.controls = new_badges

        txt_height_val.value = data["height"]
        txt_weight_val.value = data["weight"]
        txt_exp_val.value = data["base_exp"]
        txt_abilities_val.value = data["abilities"]

        for sc in STAT_CONFIG:
            s_key = sc["key"]
            raw_val = data["stats"].get(s_key, 50)
            stat_value_texts[s_key].value = str(raw_val)
            stat_progress_bars[s_key].value = min(1.0, round(raw_val / 180.0, 3))

        txt_total_stats.value = f"BASE STAT TOTAL: {data['total_stats']}"
        txt_total_stats.color = primary_hex

        bg_wrapper.update()
        asyncio.create_task(preload_neighbors(data["id"]))

    # -----------------------------------------------------------------------
    # 3. Granular Pomodoro Background Task (Updates ONLY txt_timer in-place)
    # -----------------------------------------------------------------------
    btn_timer_toggle = ft.ElevatedButton(
        text="Start Focus",
        bgcolor="#26FFFFFF",
        color="#FFFFFF",
        height=32,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    async def timer_loop() -> None:
        while True:
            await asyncio.sleep(1)
            if state["timer_running"]:
                state["timer_seconds"] = max(0, state["timer_seconds"] - 1)
                m, s = divmod(state["timer_seconds"], 60)
                txt_timer.value = f"{m:02d}:{s:02d}"
                if state["timer_seconds"] == 0:
                    state["timer_running"] = False
                    state["timer_seconds"] = 25 * 60
                    state["trainer_xp"] += 250
                    txt_trainer_xp.value = f"{state['trainer_xp']} EXP"
                    btn_timer_toggle.text = "Start Focus"
                    txt_trainer_xp.update()
                    btn_timer_toggle.update()
                txt_timer.update()

    async def on_timer_toggle(_: ft.ControlEvent) -> None:
        state["timer_running"] = not state["timer_running"]
        btn_timer_toggle.text = "Pause" if state["timer_running"] else "Start Focus"
        btn_timer_toggle.update()

    async def on_timer_reset(_: ft.ControlEvent) -> None:
        state["timer_running"] = False
        state["timer_seconds"] = 25 * 60
        txt_timer.value = "25:00"
        btn_timer_toggle.text = "Start Focus"
        txt_timer.update()
        btn_timer_toggle.update()

    btn_timer_toggle.on_click = on_timer_toggle

    # -----------------------------------------------------------------------
    # 4. Event Handlers (Buttons, Search, Keyboard Arrows)
    # -----------------------------------------------------------------------
    async def on_prev_click(_: ft.ControlEvent) -> None:
        curr = state["current_id"]
        target = curr - 1 if curr > 1 else MAX_POKEMON_ID
        await load_pokemon(target)

    async def on_next_click(_: ft.ControlEvent) -> None:
        curr = state["current_id"]
        target = curr + 1 if curr < MAX_POKEMON_ID else 1
        await load_pokemon(target)

    async def on_random_click(_: ft.ControlEvent) -> None:
        search_input.value = ""
        search_input.update()
        await load_pokemon(random.randint(1, MAX_POKEMON_ID))

    async def on_search_submit(_: ft.ControlEvent) -> None:
        q = (search_input.value or "").strip()
        if q:
            await load_pokemon(q)

    async def on_keyboard(e: ft.KeyboardEvent) -> None:
        if e.key == "Arrow Left":
            await on_prev_click(e)
        elif e.key == "Arrow Right":
            await on_next_click(e)

    search_input.on_submit = on_search_submit
    page.on_keyboard_event = on_keyboard

    # -----------------------------------------------------------------------
    # 5. Layout Assembly (Centered Glassmorphism Card + Lateral Nav Arrows)
    # -----------------------------------------------------------------------
    def _metric_chip(label: str, value_control: ft.Control, expand: bool = True) -> ft.Container:
        return ft.Container(
            expand=expand,
            bgcolor="#80090D16",
            border=ft.border.all(1, "#1AFFFFFF"),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            alignment=ft.alignment.center,
            content=ft.Column(
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(label.upper(), size=10, weight=ft.FontWeight.W_700, color="#64748B"),
                    value_control,
                ],
            ),
        )

    btn_prev = ft.IconButton(
        icon=Icons.CHEVRON_LEFT if Icons else "chevron_left",
        icon_color="#FFFFFF",
        icon_size=26,
        bgcolor="#990F172A",
        tooltip="Previous Pokémon (←)",
        on_click=on_prev_click,
    )

    btn_next = ft.IconButton(
        icon=Icons.CHEVRON_RIGHT if Icons else "chevron_right",
        icon_color="#FFFFFF",
        icon_size=26,
        bgcolor="#990F172A",
        tooltip="Next Pokémon (→)",
        on_click=on_next_click,
    )

    btn_search = ft.IconButton(
        icon=Icons.SEARCH if Icons else "search",
        icon_color="#F8FAFC",
        icon_size=18,
        bgcolor="#26FFFFFF",
        tooltip="Search Pokédex",
        on_click=on_search_submit,
    )

    btn_random = ft.ElevatedButton(
        text="Random",
        icon=Icons.SHUFFLE if Icons else "shuffle",
        bgcolor="#26FFFFFF",
        color="#FFFFFF",
        height=42,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
        on_click=on_random_click,
    )

    hero_section = ft.Container(
        expand=5,
        bgcolor="#66090D16",
        border=ft.border.all(1, "#1AFFFFFF"),
        border_radius=22,
        padding=ft.padding.symmetric(horizontal=12, vertical=16),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
            controls=[
                txt_code_pill,
                ft.Stack(
                    width=255,
                    height=198,
                    alignment=ft.alignment.center,
                    controls=[
                        txt_watermark,
                        hero_glow_orb,
                        img_wrapper,
                    ],
                ),
                txt_name,
                badges_row,
            ],
        ),
    )

    info_section = ft.Container(
        expand=7,
        padding=ft.padding.symmetric(horizontal=4, vertical=2),
        content=ft.Column(
            spacing=10,
            controls=[
                # Integrated Pomodoro Focus Bar
                ft.Container(
                    bgcolor="#80090D16",
                    border=ft.border.all(1, "#1AFFFFFF"),
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text("POKEFOCUS", size=10, weight=ft.FontWeight.W_900, color="#64748B"),
                                    txt_timer,
                                    txt_trainer_xp,
                                ],
                            ),
                            ft.Row(
                                spacing=6,
                                controls=[
                                    btn_timer_toggle,
                                    ft.TextButton(
                                        text="Reset",
                                        style=ft.ButtonStyle(color="#94A3B8"),
                                        on_click=on_timer_reset,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        _metric_chip("Height", txt_height_val),
                        _metric_chip("Weight", txt_weight_val),
                        _metric_chip("Base EXP", txt_exp_val),
                    ],
                ),
                ft.Container(
                    bgcolor="#80090D16",
                    border=ft.border.all(1, "#1AFFFFFF"),
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=14, vertical=8),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("ABILITIES", size=10, weight=ft.FontWeight.W_800, color="#64748B"),
                            txt_abilities_val,
                        ],
                    ),
                ),
                ft.Container(
                    bgcolor="#80090D16",
                    border=ft.border.all(1, "#1AFFFFFF"),
                    border_radius=16,
                    padding=ft.padding.all(14),
                    content=ft.Column(
                        spacing=7,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "BASE STATS",
                                        size=11,
                                        weight=ft.FontWeight.W_900,
                                        color="#94A3B8",
                                    ),
                                    txt_total_stats,
                                ],
                            ),
                            *stat_rows,
                        ],
                    ),
                ),
            ],
        ),
    )

    quick_picks = [
        (25, "Pikachu"),
        (6, "Charizard"),
        (94, "Gengar"),
        (658, "Greninja"),
        (448, "Lucario"),
        (150, "Mewtwo"),
        (384, "Rayquaza"),
    ]

    async def make_quick_handler(pid: int):
        search_input.value = ""
        search_input.update()
        await load_pokemon(pid)

    quick_chips_row = ft.Row(
        spacing=6,
        wrap=True,
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.Container(
                bgcolor="#1AFFFFFF",
                border=ft.border.all(1, "#22FFFFFF"),
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                ink=True,
                on_click=lambda _, pid=p_id: page.run_task(make_quick_handler, pid),
                content=ft.Text(f"#{p_id:03d} {p_name}", size=11, weight=ft.FontWeight.W_700, color="#E2E8F0"),
            )
            for p_id, p_name in quick_picks
        ],
    )

    glass_card = ft.Container(
        width=840,
        bgcolor="#BF0F172A",
        blur=ft.Blur(24, 24, ft.BlurTileMode.MIRROR),
        border=ft.border.all(1.5, "#40FACC15"),
        border_radius=28,
        padding=ft.padding.all(22),
        animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=45,
            color="#33FACC15",
            offset=ft.Offset(0, 14),
        ),
        content=ft.Column(
            spacing=12,
            tight=True,
            controls=[
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        search_input,
                        loading_ring,
                        btn_search,
                        btn_random,
                    ],
                ),
                quick_chips_row,
                error_banner,
                ft.ResponsiveRow(
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                    controls=[
                        ft.Container(col={"xs": 12, "md": 5}, content=hero_section),
                        ft.Container(col={"xs": 12, "md": 7}, content=info_section),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Tip: Use keyboard arrows (← / →) to navigate", size=11, color="#64748B"),
                        ft.Text("PokéAPI v2 • Official Anime Artwork", size=11, color="#64748B"),
                    ],
                ),
            ],
        ),
    )

    bg_wrapper = ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        padding=ft.padding.all(16),
        animate=ft.Animation(450, ft.AnimationCurve.EASE_OUT),
        gradient=ft.RadialGradient(
            center=ft.Alignment(0, -0.35),
            radius=1.15,
            colors=["#44FACC15", "#1D1907", "#06080E"],
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                btn_prev,
                glass_card,
                btn_next,
            ],
        ),
    )

    page.add(bg_wrapper)
    asyncio.create_task(timer_loop())
    await load_pokemon(25)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8501"))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port)
