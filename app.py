"""
Pomodoro timer and task tracker built with Streamlit and SQLite.
"""

from __future__ import annotations

import base64
import time
from pathlib import Path

import streamlit as st

from core import COMPANIONS, XP_PER_FOCUS_MINUTE, compute_level
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
    page_title="Dib — Pomodoro & Focus Tracker",
    page_icon="🦉",
    layout="wide",
)


def _gif_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/gif;base64,{encoded}"


def _init_session_state(profile: dict) -> None:
    st.session_state.setdefault("mode", "focus")  # 'focus' or 'break'
    st.session_state.setdefault("running", False)
    st.session_state.setdefault(
        "remaining_sec", int(profile["focus_duration"]) * 60
    )


def main() -> None:
    profile = get_profile()
    _init_session_state(profile)

    active_companion = COMPANIONS.get(profile["companion"], COMPANIONS["coruja"])
    level_info = compute_level(profile["total_xp"])

    with st.sidebar:
        st.header("Companheiro")
        selected_key = st.radio(
            "Escolha seu animal:",
            options=list(COMPANIONS.keys()),
            index=list(COMPANIONS.keys()).index(active_companion.key),
            format_func=lambda k: f"{COMPANIONS[k].name} ({COMPANIONS[k].trait})",
        )
        if selected_key != active_companion.key:
            update_companion(selected_key)
            st.rerun()

        st.divider()
        st.subheader("Duração (minutos)")
        focus_min = st.number_input(
            "Foco",
            min_value=1,
            max_value=90,
            value=int(profile["focus_duration"]),
        )
        break_min = st.number_input(
            "Pausa",
            min_value=1,
            max_value=30,
            value=int(profile["break_duration"]),
        )
        if st.button("Salvar Duração", use_container_width=True):
            update_durations(focus_min, break_min)
            st.session_state["running"] = False
            target_min = focus_min if st.session_state["mode"] == "focus" else break_min
            st.session_state["remaining_sec"] = int(target_min) * 60
            st.rerun()

    col_timer, col_side = st.columns([1.6, 1], gap="large")

    with col_timer:
        st.title("Dib")
        mode_label = "⏱️ Sessão de Foco" if st.session_state["mode"] == "focus" else "☕ Pausa Curta"
        st.subheader(mode_label)

        total_sec = (
            int(profile["focus_duration"]) * 60
            if st.session_state["mode"] == "focus"
            else int(profile["break_duration"]) * 60
        )
        rem = max(0, int(st.session_state["remaining_sec"]))
        mins, secs = divmod(rem, 60)

        st.markdown(
            f"<h1 style='font-size: 4.5rem; font-family: monospace; margin: 0.5rem 0;'>"
            f"{mins:02d}:{secs:02d}</h1>",
            unsafe_allow_html=True,
        )

        elapsed_ratio = min(1.0, max(0.0, 1.0 - (rem / max(1, total_sec))))
        st.progress(elapsed_ratio)

        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if not st.session_state["running"]:
                if st.button("▶ Iniciar", use_container_width=True, type="primary"):
                    st.session_state["running"] = True
                    st.rerun()
            else:
                if st.button("⏸ Pausar", use_container_width=True):
                    st.session_state["running"] = False
                    st.rerun()
        with b2:
            if st.button("↺ Resetar", use_container_width=True):
                st.session_state["running"] = False
                st.session_state["remaining_sec"] = total_sec
                st.rerun()
        with b3:
            if st.button("✓ Concluir Agora", use_container_width=True):
                st.session_state["running"] = False
                if st.session_state["mode"] == "focus":
                    record_focus_session(int(profile["focus_duration"]))
                    st.session_state["mode"] = "break"
                    st.session_state["remaining_sec"] = int(profile["break_duration"]) * 60
                else:
                    st.session_state["mode"] = "focus"
                    st.session_state["remaining_sec"] = int(profile["focus_duration"]) * 60
                st.rerun()
        with b4:
            next_mode = "break" if st.session_state["mode"] == "focus" else "focus"
            label = "Ir para Pausa" if next_mode == "break" else "Ir para Foco"
            if st.button(label, use_container_width=True):
                st.session_state["running"] = False
                st.session_state["mode"] = next_mode
                st.session_state["remaining_sec"] = (
                    int(profile["break_duration"]) * 60
                    if next_mode == "break"
                    else int(profile["focus_duration"]) * 60
                )
                st.rerun()

        st.divider()
        s1, s2, s3 = st.columns(3)
        s1.metric("Minutos Focados", f"{profile['total_minutes']} min")
        s2.metric("XP Acumulado", f"{profile['total_xp']} XP")
        s3.metric("Sessões Concluídas", str(profile["sessions_completed"]))

    with col_side:
        # Companion Level Card
        st.subheader(f"{active_companion.name} · Nível {level_info.level}")
        data_uri = _gif_data_uri(active_companion.sprite_path)
        if data_uri:
            st.markdown(
                f"<img src='{data_uri}' width='96' style='image-rendering: pixelated; margin-bottom: 0.5rem;' />",
                unsafe_allow_html=True,
            )
        st.caption(
            f"Perfil: **{active_companion.trait}** · Ganha {XP_PER_FOCUS_MINUTE} XP por minuto focado"
        )
        st.progress(level_info.progress_ratio)
        st.caption(
            f"{level_info.current_level_xp} / {level_info.next_level_xp} XP para o nível {level_info.level + 1}"
        )

        st.divider()

        # Task List Card
        st.subheader("Tarefas")
        with st.form("new_task_form", clear_on_submit=True):
            new_title = st.text_input("Nova tarefa", placeholder="Ex: Revisar módulo de SQL...")
            submitted = st.form_submit_button("Adicionar", use_container_width=True)
            if submitted and new_title.strip():
                add_task(new_title)
                st.rerun()

        tasks = list_tasks()
        if not tasks:
            st.caption("Nenhuma tarefa cadastrada.")
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
                if st.button("Limpar concluídas", use_container_width=True):
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
