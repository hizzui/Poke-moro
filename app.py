"""
Poke-moro — Gamified Pokémon Pomodoro Timer & Task Tracker built with Streamlit and SQLite.
Responsive across desktop and mobile viewports.
"""

from __future__ import annotations

import base64
import time
from pathlib import Path

import streamlit as st

from core import COMPANIONS, XP_PER_FOCUS_MINUTE, compute_level, resolve_companion
from storage import (
    add_task,
    clear_completed_tasks,
    get_profile,
    list_tasks,
    record_focus_session,
    toggle_task,
    update_companion,
    update_durations,
)

st.set_page_config(
    page_title="Poke-moro — Pokémon Pomodoro & Task Tracker",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _gif_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/gif;base64,{encoded}"


def _inject_responsive_css(accent_hex: str) -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --poke-accent: {accent_hex};
        }}
        .block-container {{
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 1120px !important;
        }}
        .dib-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.75rem;
            padding: 1rem 1.25rem;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(25,28,36,0.92), rgba(15,17,23,0.96));
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 5px solid var(--poke-accent);
            margin-bottom: 1.25rem;
        }}
        .dib-title {{
            font-size: clamp(1.35rem, 3.5vw, 1.85rem);
            font-weight: 800;
            letter-spacing: -0.02em;
            margin: 0;
            color: #F8FAFC;
        }}
        .dib-subtitle {{
            font-size: 0.88rem;
            color: #94A3B8;
            margin: 0.15rem 0 0 0;
        }}
        .dib-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.8rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            background: rgba(255,255,255,0.06);
            color: #F8FAFC;
            border: 1px solid var(--poke-accent);
        }}
        .timer-card {{
            text-align: center;
            padding: clamp(1.25rem, 4vw, 2.25rem) 1rem;
            border-radius: 18px;
            background: linear-gradient(180deg, rgba(22,25,34,0.9), rgba(14,16,22,0.95));
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
            margin-bottom: 1rem;
        }}
        .timer-mode-pill {{
            display: inline-block;
            padding: 0.3rem 0.9rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            background: rgba(255,255,255,0.06);
            color: var(--poke-accent);
            margin-bottom: 0.5rem;
        }}
        .timer-digits {{
            font-size: clamp(3.4rem, 14vw, 5.6rem);
            font-weight: 800;
            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
            line-height: 1.05;
            letter-spacing: 0.04em;
            margin: 0.35rem 0 0.75rem 0;
            color: #FFFFFF;
        }}
        .pokedex-card {{
            padding: 1.25rem;
            border-radius: 18px;
            background: linear-gradient(145deg, rgba(24,27,36,0.94), rgba(15,17,24,0.98));
            border: 1px solid rgba(255,255,255,0.08);
            border-top: 4px solid var(--poke-accent);
            margin-bottom: 1rem;
        }}
        .pokedex-top {{
            display: flex;
            align-items: center;
            gap: 1.1rem;
        }}
        .sprite-box {{
            width: 96px;
            height: 96px;
            min-width: 96px;
            border-radius: 16px;
            background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, rgba(15,17,23,0.95) 75%);
            border: 1px solid rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .sprite-box img {{
            max-width: 76px;
            max-height: 76px;
            image-rendering: pixelated;
        }}
        .poke-name {{
            font-size: 1.3rem;
            font-weight: 800;
            color: #F8FAFC;
            margin: 0;
        }}
        .poke-meta {{
            font-size: 0.82rem;
            color: #94A3B8;
            margin: 0.2rem 0 0.45rem 0;
        }}
        .type-pill {{
            display: inline-block;
            padding: 0.18rem 0.6rem;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            background: var(--poke-accent);
            color: #0B0D13;
        }}
        .evo-chain {{
            font-size: 0.78rem;
            color: #94A3B8;
            margin-top: 0.65rem;
            padding-top: 0.65rem;
            border-top: 1px solid rgba(255,255,255,0.07);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.65rem;
            margin: 1rem 0;
        }}
        .stat-box {{
            padding: 0.85rem 0.6rem;
            border-radius: 14px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.07);
            text-align: center;
        }}
        .stat-val {{
            font-size: clamp(1.05rem, 3vw, 1.35rem);
            font-weight: 800;
            color: #F8FAFC;
        }}
        .stat-lbl {{
            font-size: 0.73rem;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-top: 0.15rem;
        }}
        @media (max-width: 768px) {{
            .block-container {{
                padding-left: 0.85rem !important;
                padding-right: 0.85rem !important;
                padding-top: 0.9rem !important;
            }}
            .dib-header {{
                padding: 0.85rem 1rem;
            }}
            .sprite-box {{
                width: 82px;
                height: 82px;
                min-width: 82px;
            }}
            div[data-testid="stHorizontalBlock"] {{
                gap: 0.5rem !important;
            }}
            .stButton > button {{
                min-height: 2.75rem !important;
                font-weight: 600 !important;
                border-radius: 12px !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_session_state(profile: dict) -> None:
    st.session_state.setdefault("mode", "focus")
    st.session_state.setdefault("running", False)
    st.session_state.setdefault(
        "remaining_sec", int(profile["focus_duration"]) * 60
    )


def _render_settings_controls(profile: dict, active_key: str, prefix: str) -> None:
    keys = list(COMPANIONS.keys())
    selected_key = st.selectbox(
        "Partner Pokémon Line",
        options=keys,
        index=keys.index(active_key) if active_key in keys else 0,
        format_func=lambda k: (
            f"{COMPANIONS[k].name} [{COMPANIONS[k].element_type}] — "
            f"{' -> '.join(s.name for s in COMPANIONS[k].stages)}"
        ),
        key=f"{prefix}_partner_select",
    )
    if selected_key != active_key:
        update_companion(selected_key)
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        focus_min = st.number_input(
            "Focus (min)",
            min_value=1,
            max_value=90,
            value=int(profile["focus_duration"]),
            key=f"{prefix}_focus_min",
        )
    with c2:
        break_min = st.number_input(
            "Break (min)",
            min_value=1,
            max_value=30,
            value=int(profile["break_duration"]),
            key=f"{prefix}_break_min",
        )
    if st.button("Apply Timer Settings", use_container_width=True, key=f"{prefix}_save_btn"):
        update_durations(focus_min, break_min)
        st.session_state["running"] = False
        target_min = focus_min if st.session_state["mode"] == "focus" else break_min
        st.session_state["remaining_sec"] = int(target_min) * 60
        st.rerun()


def main() -> None:
    profile = get_profile()
    _init_session_state(profile)

    active_companion = resolve_companion(profile["companion"])
    level_info = compute_level(profile["total_xp"])
    current_stage = active_companion.stage_for_level(level_info.level)
    next_stage = active_companion.next_evolution(level_info.level)

    _inject_responsive_css(active_companion.accent_hex)

    # Sidebar settings (Desktop)
    with st.sidebar:
        st.header("Trainer Settings")
        _render_settings_controls(profile, active_companion.key, prefix="sidebar")

    # Top Header Banner
    st.markdown(
        f"""
        <div class="dib-header">
            <div>
                <p class="dib-title">Poke-moro — PokéFocus Trainer</p>
                <p class="dib-subtitle">Train your partner Pokémon through deep focus sessions (+{XP_PER_FOCUS_MINUTE} EXP / min)</p>
            </div>
            <span class="dib-badge">{current_stage.pokedex_code} {current_stage.name} • Lv. {level_info.level}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Mobile-friendly inline settings drawer
    with st.expander("Switch Partner Pokémon & Timer Settings", expanded=False):
        _render_settings_controls(profile, active_companion.key, prefix="inline")

    col_timer, col_side = st.columns([1.45, 1], gap="large")

    with col_timer:
        is_focus = st.session_state["mode"] == "focus"
        mode_text = "Battle Focus Session" if is_focus else "Pokémon Center Rest"
        total_sec = (
            int(profile["focus_duration"]) * 60
            if is_focus
            else int(profile["break_duration"]) * 60
        )
        rem = max(0, int(st.session_state["remaining_sec"]))
        mins, secs = divmod(rem, 60)

        st.markdown(
            f"""
            <div class="timer-card">
                <span class="timer-mode-pill">{mode_text}</span>
                <div class="timer-digits">{mins:02d}:{secs:02d}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        elapsed_ratio = min(1.0, max(0.0, 1.0 - (rem / max(1, total_sec))))
        st.progress(elapsed_ratio)

        # 2x2 responsive button layout (clean on both mobile and desktop)
        row1_a, row1_b = st.columns(2)
        with row1_a:
            if not st.session_state["running"]:
                if st.button("Start Session", use_container_width=True, type="primary"):
                    st.session_state["running"] = True
                    st.rerun()
            else:
                if st.button("Pause Session", use_container_width=True):
                    st.session_state["running"] = False
                    st.rerun()
        with row1_b:
            if st.button("Complete & Claim EXP", use_container_width=True):
                st.session_state["running"] = False
                if is_focus:
                    record_focus_session(int(profile["focus_duration"]))
                    st.session_state["mode"] = "break"
                    st.session_state["remaining_sec"] = int(profile["break_duration"]) * 60
                else:
                    st.session_state["mode"] = "focus"
                    st.session_state["remaining_sec"] = int(profile["focus_duration"]) * 60
                st.rerun()

        row2_a, row2_b = st.columns(2)
        with row2_a:
            if st.button("Reset Timer", use_container_width=True):
                st.session_state["running"] = False
                st.session_state["remaining_sec"] = total_sec
                st.rerun()
        with row2_b:
            next_mode = "break" if is_focus else "focus"
            switch_label = "Switch to Break" if next_mode == "break" else "Switch to Focus"
            if st.button(switch_label, use_container_width=True):
                st.session_state["running"] = False
                st.session_state["mode"] = next_mode
                st.session_state["remaining_sec"] = (
                    int(profile["break_duration"]) * 60
                    if next_mode == "break"
                    else int(profile["focus_duration"]) * 60
                )
                st.rerun()

        # Responsive 3-column HTML stats grid
        st.markdown(
            f"""
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-val">{profile['total_minutes']}m</div>
                    <div class="stat-lbl">Focus Time</div>
                </div>
                <div class="stat-box">
                    <div class="stat-val">{profile['total_xp']}</div>
                    <div class="stat-lbl">Total EXP</div>
                </div>
                <div class="stat-box">
                    <div class="stat-val">{profile['sessions_completed']}</div>
                    <div class="stat-lbl">Sessions</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_side:
        data_uri = _gif_data_uri(current_stage.sprite_path)
        sprite_html = f"<img src='{data_uri}' alt='{current_stage.name}' />" if data_uri else ""
        evo_parts = []
        for stg in active_companion.stages:
            if stg.pokedex_id == current_stage.pokedex_id:
                evo_parts.append(f"<strong style='color:#F8FAFC;'>{stg.name} (Lv.{stg.min_level})</strong>")
            else:
                evo_parts.append(f"{stg.name} (Lv.{stg.min_level})")
        evo_html = " -> ".join(evo_parts)
        next_evo_note = (
            f"Evolves into <strong>{next_stage.name}</strong> at <strong>Lv. {next_stage.min_level}</strong>"
            if next_stage
            else "<strong>Final Evolution Reached!</strong>"
        )

        st.markdown(
            f"""
            <div class="pokedex-card">
                <div class="pokedex-top">
                    <div class="sprite-box">{sprite_html}</div>
                    <div>
                        <span class="type-pill">{active_companion.element_type}</span>
                        <p class="poke-name">{current_stage.pokedex_code} {current_stage.name}</p>
                        <p class="poke-meta">Lv. {level_info.level} • {active_companion.trait}</p>
                    </div>
                </div>
                <div class="evo-chain">
                    <div>Evolution Line: {evo_html}</div>
                    <div style="margin-top:0.25rem;">{next_evo_note}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.progress(level_info.progress_ratio)
        st.caption(
            f"EXP: **{level_info.current_level_xp} / {level_info.next_level_xp}** to Lv. {level_info.level + 1}"
        )

        st.divider()

        st.subheader("Trainer Quests (To-Do)")
        with st.form("new_task_form", clear_on_submit=True):
            new_title = st.text_input("New quest", placeholder="e.g. Finish database migration...")
            submitted = st.form_submit_button("Add Quest", use_container_width=True)
            if submitted and new_title.strip():
                add_task(new_title)
                st.rerun()

        tasks = list_tasks()
        if not tasks:
            st.caption("No active quests yet. Add a task above to start training!")
        else:
            for item in tasks:
                checked = st.checkbox(
                    item["title"],
                    value=bool(item["done"]),
                    key=f"task_{item['id']}",
                )
                if checked != bool(item["done"]):
                    toggle_task(item["id"], checked)
                    st.rerun()

            if any(t["done"] for t in tasks):
                if st.button("Clear Completed Quests", use_container_width=True):
                    clear_completed_tasks()
                    st.rerun()

    # Live countdown tick
    if st.session_state["running"]:
        time.sleep(1)
        st.session_state["remaining_sec"] -= 1
        if st.session_state["remaining_sec"] <= 0:
            st.session_state["running"] = False
            if st.session_state["mode"] == "focus":
                record_focus_session(int(profile["focus_duration"]))
                st.session_state["mode"] = "break"
                st.session_state["remaining_sec"] = int(profile["break_duration"]) * 60
            else:
                st.session_state["mode"] = "focus"
                st.session_state["remaining_sec"] = int(profile["focus_duration"]) * 60
        st.rerun()


if __name__ == "__main__":
    main()
