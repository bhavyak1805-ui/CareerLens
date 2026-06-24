"""
nav.py — shared 'back to dashboard' control for module pages.
Call back_to_dashboard() at the top of any module page.
The full sidebar only renders on the Dashboard itself (see dashboard.py).
"""
import streamlit as st


def back_to_dashboard():
    """Small top-left button that returns to the Dashboard."""
    if st.button("← Dashboard", key="shared_back_to_dash"):
        st.session_state.active_module = None
        st.rerun()