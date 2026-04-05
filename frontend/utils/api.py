"""
API Utility
-----------
All HTTP calls to the FastAPI backend go through this module.
Every function takes a token (str | None) and returns parsed JSON or raises.
"""

import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")


def _headers(token: str | None = None) -> dict:
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _handle(response: requests.Response) -> dict | list:
    """Raise a Streamlit error on non-2xx, otherwise return JSON."""
    try:
        data = response.json()
    except Exception:
        data = {"detail": response.text}

    if response.status_code == 401:
        # Don't trigger session expiry logic if the user is merely typing a wrong password during login
        if "login" not in response.url:
            st.session_state.clear()
            st.error("Session expired. Please log in again.")
            st.stop()

    if not response.ok:
        detail = data.get("detail", "Unknown error") if isinstance(data, dict) else str(data)
        raise ValueError(detail)

    return data


# ── Auth ─────────────────────────────────────────────────────────────────────

def register(name: str, email: str, password: str) -> dict:
    r = requests.post(
        f"{API_URL}/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    return _handle(r)


def login(email: str, password: str) -> dict:
    r = requests.post(
        f"{API_URL}/auth/login",
        json={"email": email, "password": password},
    )
    return _handle(r)


def logout(token: str) -> None:
    requests.post(f"{API_URL}/auth/logout", headers=_headers(token))


# ── Profile ───────────────────────────────────────────────────────────────────

def create_profile(token: str, payload: dict) -> dict:
    r = requests.post(f"{API_URL}/profile/create", json=payload, headers=_headers(token))
    return _handle(r)


def update_profile(token: str, payload: dict) -> dict:
    r = requests.put(f"{API_URL}/profile/update", json=payload, headers=_headers(token))
    return _handle(r)


def get_my_profile(token: str) -> dict | None:
    r = requests.get(f"{API_URL}/profile/me", headers=_headers(token))
    if r.status_code == 404:
        return None
    return _handle(r)


# ── Questionnaire ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_questions(token: str) -> list:
    r = requests.get(f"{API_URL}/questionnaire/questions", headers=_headers(token))
    data = _handle(r)
    return data.get("questions", [])


def submit_questionnaire(token: str, answers: list[dict]) -> dict:
    r = requests.post(
        f"{API_URL}/questionnaire/submit",
        json={"answers": answers},
        headers=_headers(token),
    )
    return _handle(r)


# ── Portfolio ─────────────────────────────────────────────────────────────────

def generate_portfolio(token: str) -> dict:
    r = requests.post(f"{API_URL}/portfolio/generate", headers=_headers(token))
    return _handle(r)


def get_current_portfolio(token: str) -> dict | None:
    r = requests.get(f"{API_URL}/portfolio/current", headers=_headers(token))
    if r.status_code == 404:
        return None
    return _handle(r)


@st.cache_data(ttl=60, show_spinner=False)
def get_portfolio_history(token: str) -> list:
    r = requests.get(f"{API_URL}/portfolio/history", headers=_headers(token))
    data = _handle(r)
    return data if isinstance(data, list) else []


@st.cache_data(ttl=60, show_spinner=False)
def get_portfolio_summary(token: str) -> list:
    r = requests.get(f"{API_URL}/portfolio/summary", headers=_headers(token))
    if r.status_code == 404:
        return []
    return _handle(r)


@st.cache_data(ttl=60, show_spinner=False)
def get_expected_returns(token: str) -> dict | None:
    r = requests.get(f"{API_URL}/portfolio/expected-returns", headers=_headers(token))
    if r.status_code == 404:
        return None
    return _handle(r)


@st.cache_data(ttl=300, show_spinner=False)
def compare_portfolio(token: str, risk_level: str) -> dict:
    r = requests.get(f"{API_URL}/portfolio/compare/{risk_level}", headers=_headers(token))
    return _handle(r)


# ── Reference ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_instruments(token: str) -> list:
    r = requests.get(f"{API_URL}/instruments", headers=_headers(token))
    return _handle(r)


@st.cache_data(ttl=3600, show_spinner=False)
def get_risk_profiles(token: str) -> list:
    r = requests.get(f"{API_URL}/risk-profiles", headers=_headers(token))
    return _handle(r)


@st.cache_data(ttl=3600, show_spinner=False)
def get_portfolio_models(token: str) -> list:
    r = requests.get(f"{API_URL}/portfolio-models", headers=_headers(token))
    return _handle(r)
