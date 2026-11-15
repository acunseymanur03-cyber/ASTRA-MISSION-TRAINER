import math
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

try:
    from deep_translator import GoogleTranslator
except Exception:  # package missing -> English fallback
    GoogleTranslator = None

st.set_page_config(page_title="ASTRA MISSION TRAINER", page_icon="🚀", layout="wide")

# =============================================================================
# LANGUAGES (11)
# =============================================================================
LANGS = {
    "en": ("English", "en"),
    "tr": ("Türkçe", "tr"),
    "es": ("Español", "es"),
    "fr": ("Français", "fr"),
    "de": ("Deutsch", "de"),
    "pt": ("Português", "pt"),
    "ar": ("العربية", "ar"),
    "ru": ("Русский", "ru"),
    "zh": ("中文", "zh-CN"),
    "ja": ("日本語", "ja"),
    "hi": ("हिन्दी", "hi"),
}
LK = list(LANGS)  # order used by the hand-translated CORE table below


def _core(*vals):
    return dict(zip(LK, vals))


# Hand-translated core interface (always works, even offline)
CORE = {
    "tagline": _core(
        "Mission simulation and emergency decision training for young astronauts",
        "Genç astronotlar için görev simülasyonu ve acil durum karar eğitimi",
        "Simulación de misiones y entrenamiento de decisiones de emergencia para jóvenes astronautas",
        "Simulation de missions et entraînement à la décision d'urgence pour jeunes astronautes",
        "Missionssimulation und Notfall-Entscheidungstraining für junge Astronauten",
        "Simulação de missões e treino de decisões de emergência para jovens astronautas",
        "محاكاة المهام والتدريب على اتخاذ القرار في الطوارئ لرواد الفضاء الشباب",
        "Симуляция миссий и тренировка принятия решений в аварийных ситуациях для юных астронавтов",
        "面向青少年宇航员的任务模拟与紧急决策训练",
        "若手宇宙飛行士のためのミッションシミュレーションと緊急時判断トレーニング",
        "युवा अंतरिक्ष यात्रियों के लिए मिशन सिमुलेशन और आपातकालीन निर्णय प्रशिक्षण",
    ),
    "tab_mission": _core("Mission", "Görev", "Misión", "Mission", "Mission", "Missão", "المهمة", "Миссия", "任务", "ミッション", "मिशन"),
    "tab_base": _core("Moon Base", "Ay Üssü", "Base lunar", "Base lunaire", "Mondbasis", "Base lunar", "القاعدة القمرية", "Лунная база", "月球基地", "月面基地", "चंद्र अड्डा"),
    "tab_orbit": _core("Orbit", "Yörünge", "Órbita", "Orbite", "Umlaufbahn", "Órbita", "المدار", "Орбита", "轨道", "軌道", "कक्षा"),
    "tab_gravity": _core("Gravity", "Yerçekimi", "Gravedad", "Gravité", "Schwerkraft", "Gravidade", "الجاذبية", "Гравитация", "重力", "重力", "गुरुत्व"),
    "tab_life": _core("Life Support", "Yaşam Destek", "Soporte vital", "Survie", "Lebenserhaltung", "Suporte vital", "دعم الحياة", "Жизнеобеспечение", "生命保障", "生命維持", "जीवन समर्थन"),
    "tab_reentry": _core("Re-entry", "Dönüş", "Reentrada", "Rentrée", "Wiedereintritt", "Reentrada", "العودة", "Возвращение", "再入", "再突入", "पुनःप्रवेश"),
    "tab_mars": _core("Mars Landing", "Mars İniş", "Aterrizaje en Marte", "Atterrissage Mars", "Mars-Landung", "Pouso em Marte", "الهبوط على المريخ", "Посадка на Марс", "火星着陆", "火星着陸", "मंगल लैंडिंग"),
    "tab_exo": _core("Exoplanets", "Ötegezegen", "Exoplanetas", "Exoplanètes", "Exoplaneten", "Exoplanetas", "الكواكب الخارجية", "Экзопланеты", "系外行星", "系外惑星", "बहिर्ग्रह"),
    "tab_defense": _core("Planet Defense", "Gezegen Savunması", "Defensa planetaria", "Défense planétaire", "Planetenabwehr", "Defesa planetária", "الدفاع الكوكبي", "Защита планеты", "行星防御", "惑星防衛", "ग्रह रक्षा"),
    "tab_moon": _core("Moon Phases", "Ay Evreleri", "Fases lunares", "Phases lunaires", "Mondphasen", "Fases da Lua", "أطوار القمر", "Фазы Луны", "月相", "月の満ち欠け", "चंद्र कलाएँ"),
    "tab_academy": _core("Academy", "Akademi", "Academia", "Académie", "Akademie", "Academia", "الأكاديمية", "Академия", "学院", "アカデミー", "अकादमी"),
    "restart": _core("Restart", "Baştan başla", "Reiniciar", "Recommencer", "Neustart", "Reiniciar", "إعادة البدء", "Заново", "重新开始", "最初から", "फिर से शुरू"),
    "start": _core("Launch mission", "Göreve başla", "Iniciar misión", "Lancer la mission", "Mission starten", "Iniciar missão", "ابدأ المهمة", "Начать миссию", "开始任务", "ミッション開始", "मिशन शुरू करें"),
    "next": _core("Next", "Sonraki", "Siguiente", "Suivant", "Weiter", "Próximo", "التالي", "Далее", "下一步", "次へ", "अगला"),
}

# =============================================================================
# STATE
# =============================================================================
ss = st.session_state
ss.setdefault("lang", "en")
ss.setdefault("done", set())
ss.setdefault("orb_alt", 400)


def C(key):
    return CORE[key].get(ss.lang) or CORE[key]["en"]


# =============================================================================
# AUTO-TRANSLATION (cached, parallel, safe fallback to English)
# =============================================================================
@st.cache_resource
def _store():
    return {"d": {}, "fails": 0, "blocked_until": 0.0}


def _translate_one(text, lang):
    """Runs in worker threads: must NOT touch st.session_state."""
    if GoogleTranslator is None:
        return None
    for attempt in range(2):
        try:
            out = GoogleTranslator(source="en", target=LANGS[lang][1]).translate(text)
            if out:
                return out
        except Exception:
            time.sleep(0.6)
    return None


def _translate_many(texts, lang):
    """Translate many strings in ONE request (joined by newlines); split on mismatch."""
    if not texts or GoogleTranslator is None:
        return {}
    if len(texts) == 1:
        r = _translate_one(texts[0], lang)
        return {texts[0]: r} if r else {}
    try:
        res = GoogleTranslator(source="en", target=LANGS[lang][1]).translate("\n".join(texts))
    except Exception:
        time.sleep(1.0)
        return {}
    parts = (res or "").split("\n")
    if len(parts) == len(texts) and all(p.strip() for p in parts):
        return dict(zip(texts, parts))
    mid = len(texts) // 2
    out = _translate_many(texts[:mid], lang)
    out.update(_translate_many(texts[mid:], lang))
    return out


def T(text):
    """Lookup only (fast). Strings are translated in prewarm() / background thread."""
    if ss.lang == "en" or not text:
        return text
    return _store()["d"].get((ss.lang, text), text)


def _chunks(items, n):
    return [items[i:i + n] for i in range(0, len(items), n)]


def prewarm(texts):
    lang = ss.lang
    if lang == "en" or GoogleTranslator is None:
        return
    s = _store()
    if time.time() < s["blocked_until"]:
        return
    todo = [t for t in dict.fromkeys(texts) if (lang, t) not in s["d"]]
    if not todo:
        return
    with st.spinner("🌐 ..."):
        with ThreadPoolExecutor(max_workers=3) as ex:
            results = list(ex.map(lambda c: _translate_many(c, lang), _chunks(todo, 12)))
    got = 0
    for res in results:
        for t, r in res.items():
            s["d"][(lang, t)] = r
            got += 1
    if got == 0:
        s["blocked_until"] = time.time() + 15


def _bg_warm(texts):
    """Pre-translate every language once per server start so visitors get instant results."""
    s = _store()
    for lang in LK[1:]:
        todo = [t for t in texts if (lang, t) not in s["d"]]
        for chunk in _chunks(todo, 12):
            for t, r in _translate_many(chunk, lang).items():
                s["d"][(lang, t)] = r
            time.sleep(0.3)


# =============================================================================
# CONTENT
# =============================================================================
def ev(title, story, fact, best, ok, bad):
    return {
        "title": title, "story": story, "fact": fact,
        "choices": [
            {"text": best[0], "fx": best[1], "pts": 100, "why": best[2]},
            {"text": ok[0], "fx": ok[1], "pts": 50, "why": ok[2]},
            {"text": bad[0], "fx": bad[1], "pts": 0, "why": bad[2]},
        ],
    }


EVENTS = [
    ev("Stuck airlock",
       "After your spacewalk the airlock door will not seal and the crew is waiting inside.",
       "Astronauts exit through an airlock that is depressurized, so the main cabin stays pressurized.",
       ("Re-check the seals, run the airlock checklist and ask Mission Control for help", {"p": -5, "m": 5}, "Methodical checks with ground support solve most hardware faults."),
       ("Try the door again several times", {"p": -10, "m": -5}, "Repeating the same action rarely fixes a seal fault."),
       ("Force the door with a tool", {"p": -15, "o": -25}, "Forcing hardware can break the seal and damage the airlock.")),
    ev("Power loss",
       "One solar array lost its orientation and power generation dropped.",
       "The International Space Station gets its power from huge solar arrays, and non-critical systems are shut down when needed.",
       ("Switch to essential-only power and shut down non-critical systems", {"p": -5}, "Life support and communications come first: power is rationed by priority."),
       ("Shut down only the science lab", {"p": -15}, "It saves some power, but not enough."),
       ("Restart all systems at once", {"p": -35, "m": -5}, "Restarting everything causes a power surge and makes things worse.")),
    ev("Communication blackout",
       "Contact with Mission Control is lost. Only static on the radio.",
       "Spacecraft lose contact with Earth when passing behind the Moon, so there are prepared procedures for it.",
       ("Follow the lost-comm checklist and switch to the backup antenna", {"p": -5}, "Staying calm and following the procedure is the safest path."),
       ("Wait quietly without doing anything", {"m": -10}, "Waiting alone is not enough: backup options must be tried."),
       ("Do an unplanned engine burn to fix the position", {"f": -30, "m": -5}, "Maneuvering without ground control wastes fuel and can disturb the trajectory.")),
    ev("Cabin fire alarm",
       "Smoke is coming from an equipment rack and the fire alarm is sounding.",
       "Space stations carry masks and CO2 extinguishers for fire emergencies.",
       ("Cut power to the equipment, put on masks, use the CO2 extinguisher", {"o": -5, "p": -10}, "Cutting power removes the ignition source and masks protect you from smoke."),
       ("Use the extinguisher but keep the equipment powered", {"o": -10, "p": -15}, "With power still on, the fire can restart."),
       ("Open the vent to space to remove the smoke", {"o": -35, "m": -10}, "Venting cabin air to space endangers the whole crew.")),
    ev("Crew health",
       "A crew member feels dizzy and nauseous.",
       "Many astronauts feel space motion sickness during their first days in weightlessness.",
       ("Let them rest, drink water and consult the flight surgeon by radio", {"m": 10}, "Rest and medical advice protect health and raise crew morale."),
       ("Give them a hard task to distract them", {"m": -10}, "Pushing a sick crew member can make things worse."),
       ("Ignore it and keep the schedule", {"m": -25}, "Crew health is part of the mission, so symptoms are taken seriously.")),
    ev("Re-entry preparation",
       "Atmospheric re-entry is approaching. You must check the heat shield and fuel.",
       "During re-entry the capsule faces extreme heat, and the heat shield protects the crew.",
       ("Run the full checklist with Mission Control and verify heat shield and fuel", {"f": -10, "m": 5}, "Checklists reduce errors: nothing is skipped at a critical stage."),
       ("Skip two checklist items to save time", {"f": -5, "m": -5}, "Small shortcuts can turn into big risks."),
       ("Start re-entry immediately without verification", {"p": -20, "f": -20}, "In an unverified re-entry, mistakes cannot be undone.")),
    ev("Robotic arm jam",
       "The robotic arm froze while holding a heavy supply module.",
       "Robotic arms like Canadarm2 help move cargo and assist astronauts outside the ISS.",
       ("Stop all arm motion, switch to backup control and follow the safe-hold procedure", {"p": -5, "m": 5}, "A safe hold prevents damage while you diagnose the fault."),
       ("Try to move the arm again slowly", {"p": -10, "m": -5}, "Moving a faulty arm can make the problem worse."),
       ("Release the module without checking", {"f": -10, "m": -20}, "A loose module can drift into the station or be lost.")),
    ev("Solar storm warning",
       "Mission Control warns of a strong solar storm and radiation levels are rising.",
       "Solar storms raise radiation, so astronauts shelter in the most shielded parts of the spacecraft.",
       ("Move the crew to the shielded shelter area and monitor the dosimeters", {"m": 5, "p": -5}, "Shielding and monitoring reduce the radiation dose."),
       ("Wear protective vests but continue the planned work", {"m": -10}, "Vests help, but staying exposed is still risky."),
       ("Continue the spacewalk as scheduled", {"m": -30, "o": -10}, "Radiation exposure outside is the biggest danger.")),
    ev("Water recycler failure",
       "The water recycling unit shut down and the tank level is dropping.",
       "The ISS recycles most of its water, including moisture from the air and urine.",
       ("Switch to reserve water, ration use and follow the repair guide", {"p": -5, "m": 5}, "Rationing buys time while the repair is done."),
       ("Ration water only and wait", {"m": -15}, "Rationing alone does not fix the unit."),
       ("Use water freely and hope the unit recovers", {"m": -30, "p": -10}, "Wasting reserves can leave the crew without water.")),
    ev("Docking misalignment",
       "The capsule drifts off-axis while approaching the station for docking.",
       "Spacecraft dock at speeds of only about 10 centimeters per second.",
       ("Stop the approach, back off, realign and retry", {"f": -8, "m": 5}, "Aborting and retrying is routine and safe."),
       ("Continue slowly and hope it corrects itself", {"f": -5, "m": -10}, "Hoping is not a plan, and the misalignment can grow."),
       ("Speed up to force the docking", {"f": -20, "p": -15, "m": -15}, "Forcing a dock can damage both spacecraft.")),
]

BODIES = {
    "Mercury": 3.70, "Venus": 8.87, "Earth": 9.81, "Moon": 1.62, "Mars": 3.71,
    "Jupiter": 24.79, "Saturn": 10.44, "Uranus": 8.69, "Neptune": 11.15, "Pluto": 0.62,
}

BADGES = {
    "mission": "🛰️", "base": "🌙", "orbit": "🌍", "reentry": "🔥", "mars": "🔴", "exo": "🔭", "defense": "☄️",
}

STARS = {"Red dwarf": 0.04, "Sun-like star": 1.0, "Bright white star": 5.0}  # luminosity vs Sun
YEARS = {"Mercury": 0.2408, "Venus": 0.6152, "Earth": 1.0, "Mars": 1.8808, "Jupiter": 11.862, "Saturn": 29.457, "Uranus": 84.02, "Neptune": 164.8}
PHASE_NAMES = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous", "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]

RANKS = [(500, "Commander 🥇"), (350, "Pilot 🥈"), (200, "Cadet 🥉"), (0, "Trainee 🚀")]


def rank_of(score):
    for th, name in RANKS:
        if score >= th:
            return name
    return RANKS[-1][1]


def mark(key):
    ss.done.add(key)


def show_chart(ch, container=True):
    ch = ch.configure(background="transparent").configure_axis(
        labelColor="#dbe4ff", titleColor="#dbe4ff", gridColor="#2a3a7a",
        domainColor="#7aa2ff", tickColor="#7aa2ff",
    ).configure_view(strokeWidth=0)
    st.altair_chart(ch, use_container_width=container, theme=None)


def bar_chart(df):
    d = df.reset_index().iloc[:, :2]
    d.columns = ["x", "y"]
    show_chart(alt.Chart(d).mark_bar(color="#4b8bff").encode(
        x=alt.X("x:N", sort=None, title=None, axis=alt.Axis(labelAngle=-35)),
        y=alt.Y("y:Q", title=None), tooltip=["x", "y"]).properties(height=280))


def line_chart(df):
    d = df.reset_index().iloc[:, :2]
    d.columns = ["x", "y"]
    show_chart(alt.Chart(d).mark_line(color="#ff9f43", strokeWidth=3).encode(
        x=alt.X("x:Q", title=None), y=alt.Y("y:Q", title=None)).properties(height=240))


# ---- collect every string that should be pre-translated -----------------------
try:
    with open(__file__, encoding="utf-8") as _f:
        _src = _f.read()
except Exception:
    _src = ""
ALL_TEXTS = [a or b for a, b in re.findall(r'\bT\(\s*(?:"([^"\n]+)"|\'([^\'\n]+)\')\s*\)', _src)]
for _e in EVENTS:
    ALL_TEXTS += [_e["title"], _e["story"], _e["fact"]]
    for _c in _e["choices"]:
        ALL_TEXTS += [_c["text"], _c["why"]]
ALL_TEXTS += list(BODIES) + [n for _, n in RANKS] + list(STARS) + PHASE_NAMES
ALL_TEXTS = list(dict.fromkeys(ALL_TEXTS))

_s0 = _store()
if not _s0.get("bg") and GoogleTranslator is not None:
    _s0["bg"] = True
    threading.Thread(target=_bg_warm, args=(list(ALL_TEXTS),), daemon=True).start()

# =============================================================================
# STYLE + SIDEBAR
# =============================================================================
_rs = random.Random(11)
_layers, _sizes = [], []
for _tile in (260, 410, 640):
    for _ in range(7):
        _x, _y = _rs.randint(5, _tile - 5), _rs.randint(5, _tile - 5)
        _px = _rs.choice([1, 1, 1.5, 2])
        _col = _rs.choice(["#ffffff", "#cfe0ff", "#fff3d6"])
        _layers.append(f"radial-gradient({_px}px {_px}px at {_x}px {_y}px, {_col}, transparent)")
        _sizes.append(f"{_tile}px {_tile}px")
_layers += [
    "radial-gradient(ellipse 100% 26% at 50% 112%, rgba(120,190,255,.95) 0%, rgba(40,110,220,.80) 40%, rgba(10,30,90,0) 72%)",
    "radial-gradient(ellipse at 12% 18%, rgba(120,70,210,.38), transparent 46%)",
    "radial-gradient(ellipse at 88% 30%, rgba(30,110,230,.30), transparent 44%)",
    "radial-gradient(ellipse at 50% 60%, rgba(10,18,60,.9), #02030a 80%)",
]
_sizes += ["100% 100%"] * 4

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&display=swap');
html, body {background-color:#02030a !important; background-image: __BG__ !important;
  background-size: __SZ__ !important; background-repeat: repeat !important; background-attachment: fixed !important;}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] {background: transparent !important;}
[data-testid="stSidebar"] > div:first-child {background: rgba(6,10,32,.84) !important; backdrop-filter: blur(6px);}
.block-container, [data-testid="stMainBlockContainer"] {background: rgba(4,8,26,.58); border:1px solid rgba(122,162,255,.20);
  border-radius:18px; padding: 1.4rem 2rem 3rem !important; margin-top:.8rem; backdrop-filter: blur(5px); max-width: 1250px;}
h1, h2, h3, h4 {font-family:'Orbitron', sans-serif !important; letter-spacing:.5px;}
[data-testid="stMetric"] {background: rgba(20,32,80,.55); border:1px solid rgba(122,162,255,.30); border-radius:12px; padding:10px 14px;}
.stTabs [data-baseweb="tab-list"] {gap:4px; flex-wrap: wrap;}
.stTabs [data-baseweb="tab"] {background: rgba(25,40,100,.45); border-radius:10px 10px 0 0; padding: 8px 14px;}
.stTabs [aria-selected="true"] {background: rgba(70,110,255,.55) !important;}
div.stButton > button {border-radius:12px; border:1px solid #7aa2ff; background: rgba(40,70,170,.45); color:#fff; transition: all .2s;}
div.stButton > button:hover {box-shadow: 0 0 14px rgba(122,162,255,.8); border-color:#fff; color:#fff;}
.hero {display:flex; flex-wrap:wrap; align-items:center; gap:1.2rem; padding:1.1rem 1.4rem; border-radius:16px;
  background: linear-gradient(135deg, rgba(11,16,38,.85), rgba(27,42,107,.75) 55%, rgba(75,42,123,.75));
  border:1px solid rgba(122,162,255,.35); box-shadow: 0 0 30px rgba(80,120,255,.25); margin-bottom:1rem;}
.hero h1 {margin:0; font-size:1.8rem; letter-spacing:3px; color:#fff;}
.hero p {margin:.3rem 0 .5rem 0; color:#dbe4ff; opacity:.92;}
.pill {display:inline-block; font-size:.7rem; letter-spacing:1px; padding:3px 10px; margin:2px 6px 2px 0; border-radius:999px;
  border:1px solid rgba(122,162,255,.5); background: rgba(20,32,80,.6); color:#cfe0ff; font-family: monospace;}
.dot {display:inline-block; width:8px; height:8px; border-radius:50%; background:#3cff9e; margin-right:6px; animation: blink 1.4s infinite;}
.sat {transform-box: view-box; transform-origin: 50px 50px; animation: spin 9s linear infinite;}
@keyframes spin {to {transform: rotate(360deg);}}
@keyframes blink {50% {opacity:.25;}}
.event {padding: 1rem 1.2rem; border-left: 5px solid #ff4b4b; background: rgba(255,75,75,.12); border-radius: 8px; margin: .6rem 0;}
.fact {padding: .7rem 1rem; border-left: 5px solid #4b8bff; background: rgba(75,139,255,.12); border-radius: 8px; margin: .6rem 0;}
.stApp :is(p, span, label, li, small, h1, h2, h3, h4, h5, h6, td, th, summary, div[data-testid="stMarkdownContainer"],
  div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"], div[data-testid="stCaptionContainer"],
  div[data-testid="stWidgetLabel"]) {color: #e8ecff !important;}
.stApp [data-testid="stMetricLabel"] p {color: #b9c8ff !important;}
.stApp [data-testid="stMetricValue"] {color: #7fffd4 !important;}
.stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"],
.stApp input, .stApp textarea {background-color: rgba(20,32,80,.85) !important; color: #ffffff !important; border-color: rgba(122,162,255,.5) !important;}
.stApp [data-baseweb="select"] *, .stApp [data-baseweb="tag"] span {color: #ffffff !important;}
[data-baseweb="popover"] > div, [data-baseweb="popover"] ul, [data-baseweb="menu"], ul[role="listbox"] {background: #0c1230 !important;}
[data-baseweb="popover"] li, [data-baseweb="popover"] li * , [data-baseweb="menu"] li, ul[role="listbox"] li {color: #ffffff !important; background: transparent !important;}
[data-baseweb="popover"] li:hover, ul[role="listbox"] li:hover {background: rgba(75,139,255,.45) !important;}
.stApp [data-testid="stExpander"] details {background: rgba(20,32,80,.45); border: 1px solid rgba(122,162,255,.35); border-radius: 10px;}
.stApp [data-testid="stSlider"] [data-testid="stTickBarMin"], .stApp [data-testid="stSlider"] [data-testid="stTickBarMax"] {color: #b9c8ff !important;}
.stApp [data-testid="stAlert"] {background: rgba(20,32,80,.55) !important; border: 1px solid rgba(122,162,255,.35);}
.stApp [data-testid="stDataFrame"] {filter: invert(0);}
html {color-scheme: dark !important;}
.stApp, .stApp * {color: #e8ecff !important;}
.stApp [data-testid="stMetricLabel"] p, .stApp [data-testid="stMetricLabel"] {color: #b9c8ff !important;}
.stApp [data-testid="stMetricValue"], .stApp [data-testid="stMetricValue"] * {color: #7fffd4 !important;}
.stApp input::placeholder, .stApp textarea::placeholder {color: #9fb0e8 !important; opacity: 1 !important;}
.stApp [data-baseweb="select"] *, .stApp input, .stApp textarea {color: #ffffff !important;}
.stApp a {color: #8fb4ff !important;}
</style>
"""
st.markdown(_CSS.replace("__BG__", ", ".join(_layers)).replace("__SZ__", ", ".join(_sizes)), unsafe_allow_html=True)

with st.sidebar:
    st.selectbox("🌐 Language", LK, format_func=lambda k: LANGS[k][0], key="lang")

if ss.lang == "ar":
    st.markdown(
        "<style>.stMarkdown, .stButton, label, p, h1, h2, h3 {direction: rtl; text-align: right;}</style>",
        unsafe_allow_html=True,
    )

prewarm(ALL_TEXTS)

with st.sidebar:
    st.markdown("### 🏅 " + T("Explorer badges"))
    st.progress(len(ss.done) / len(BADGES))
    st.write(" ".join(icon if key in ss.done else "🔒" for key, icon in BADGES.items()))
    st.caption(T("Earn all 7 badges: finish the mission, build a working Moon base, find geostationary orbit, survive re-entry, land on Mars, find a habitable planet, save Earth from an asteroid."))
    if ss.lang != "en":
        _all = set(ALL_TEXTS)
        _d = _store()["d"]
        _pct = sum(1 for _t in _all if (ss.lang, _t) in _d) / max(1, len(_all))
        st.progress(_pct, text=f"🌐 {_pct * 100:.0f}%")
        if _pct < 1.0 and st.button("🔁 Retry translation"):
            _store()["blocked_until"] = 0.0
            _store()["fails"] = 0
            st.rerun()
    if st.button("🔄 " + C("restart")):
        for k in list(ss.keys()):
            if k not in ("lang",):
                del ss[k]
        st.rerun()

st.markdown(
    f"""
    <div class="hero">
      <div class="patch"><svg width="92" height="92" viewBox="0 0 100 100"><defs><radialGradient id="eg" cx="40%" cy="35%"><stop offset="0" stop-color="#7fc4ff"/><stop offset="1" stop-color="#0b2a78"/></radialGradient></defs><circle cx="50" cy="50" r="47" fill="#050a22" stroke="#7aa2ff" stroke-width="3"/><circle cx="50" cy="50" r="40" fill="none" stroke="#c7d6ff" stroke-width="1" stroke-dasharray="2 4"/><circle cx="50" cy="56" r="22" fill="url(#eg)"/><ellipse cx="50" cy="50" rx="40" ry="14" fill="none" stroke="#ffd36e" stroke-width="1.6" transform="rotate(-25 50 50)"/><g class="sat"><circle cx="90" cy="50" r="3.2" fill="#ffd36e"/></g><path d="M50 10 L54 22 L50 19 L46 22 Z" fill="#fff"/></svg></div>
      <div>
        <h1>ASTRA MISSION TRAINER</h1>
        <p>{C('tagline')}</p>
        <div><span class="pill"><i class="dot"></i>SIMULATION ONLINE</span><span class="pill">11 LANGUAGES</span><span class="pill">10 LABS</span><span class="pill">NASA SPACE APPS CHALLENGE 2026</span></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if ss.lang != "en" and GoogleTranslator is None:
    st.caption("Auto-translation package not installed. Core interface is translated; details are shown in English.")

tabs = st.tabs([
    "🛰️ " + C("tab_mission"), "🌙 " + C("tab_base"), "🌍 " + C("tab_orbit"),
    "🪐 " + C("tab_gravity"), "🫁 " + C("tab_life"), "🔥 " + C("tab_reentry"),
    "🔴 " + C("tab_mars"), "🔭 " + C("tab_exo"), "☄️ " + C("tab_defense"), "🌗 " + C("tab_moon"),
])

# =============================================================================
# 1) MISSION CAMPAIGN (random 6 of 10 emergencies, branching consequences)
# =============================================================================
def m_reset():
    ss.m_started = False
    ss.m_idx = []
    ss.m_step = 0
    ss.m_stats = {"o": 100, "p": 100, "f": 100, "m": 100}
    ss.m_score = 0
    ss.m_hist = []
    ss.m_phase = "choose"
    ss.m_failed = False
    ss.m_order = [0, 1, 2]
    ss.m_last = None


if "m_started" not in ss:
    m_reset()


def m_new_order():
    o = [0, 1, 2]
    random.shuffle(o)
    ss.m_order = o


def m_start():
    ss.m_started = True
    ss.m_idx = random.sample(range(len(EVENTS)), 6)
    ss.m_step = 0
    ss.m_stats = {"o": 100, "p": 100, "f": 100, "m": 100}
    ss.m_score = 0
    ss.m_hist = []
    ss.m_failed = False
    ss.m_phase = "choose"
    m_new_order()


def m_choose(i):
    ch = EVENTS[ss.m_idx[ss.m_step]]["choices"][i]
    for k, v in ch["fx"].items():
        ss.m_stats[k] = max(0, min(100, ss.m_stats[k] + v))
    ss.m_score += ch["pts"]
    ss.m_hist.append((ss.m_idx[ss.m_step], i))
    ss.m_last = i
    ss.m_phase = "feedback"
    if ss.m_stats["o"] <= 0 or ss.m_stats["p"] <= 0:
        ss.m_failed = True


def m_next():
    ss.m_step += 1
    if ss.m_failed or ss.m_step >= 6:
        ss.m_phase = "end"
    else:
        ss.m_phase = "choose"
        m_new_order()


def m_stats_view():
    cols = st.columns(4)
    items = [("o", "🫁", T("Oxygen")), ("p", "⚡", T("Power")), ("f", "⛽", T("Fuel")), ("m", "😊", T("Morale"))]
    for col, (k, icon, name) in zip(cols, items):
        with col:
            st.metric(f"{icon} {name}", f"{ss.m_stats[k]}%")
            st.progress(ss.m_stats[k] / 100)


with tabs[0]:
    if not ss.m_started:
        st.info(T("Artemis-Junior mission: on the way home from lunar orbit, 6 random emergencies (out of 10) are waiting for you. If oxygen or power reaches zero, the mission fails. Every decision matters."))
        ss.callsign = st.text_input(T("Your callsign"), value=ss.get("callsign", "Cadet"))
        st.button("🚀 " + C("start"), type="primary", on_click=m_start)
    elif ss.m_phase in ("choose", "feedback"):
        e = EVENTS[ss.m_idx[ss.m_step]]
        st.caption(f"{T('Event')} {ss.m_step + 1}/6  •  {T('Score')}: {ss.m_score}")
        m_stats_view()
        st.markdown(f'<div class="event"><b>⚠️ {T(e["title"])}</b><br>{T(e["story"])}</div>', unsafe_allow_html=True)
        if ss.m_phase == "choose":
            st.subheader(T("Make your decision:"))
            for i in ss.m_order:
                st.button(T(e["choices"][i]["text"]), key=f"mc_{ss.m_step}_{i}", on_click=m_choose, args=(i,), use_container_width=True)
        else:
            ch = e["choices"][ss.m_last]
            icon = {100: "✅", 50: "⚠️", 0: "❌"}[ch["pts"]]
            box = {100: st.success, 50: st.warning, 0: st.error}[ch["pts"]]
            box(f"{icon} {T(ch['why'])}  (+{ch['pts']})")
            st.markdown(f'<div class="fact">🔭 {T(e["fact"])}</div>', unsafe_allow_html=True)
            last = ss.m_step >= 5 or ss.m_failed
            st.button(("📋 " + T("See mission debrief")) if last else ("➡️ " + C("next")), type="primary", on_click=m_next)
    else:
        if ss.m_failed:
            st.error("💥 " + T("MISSION FAILED. Critical systems collapsed."))
        else:
            st.success("🎉 " + T("MISSION COMPLETE! The crew returned safely to Earth."))
            st.balloons()
            mark("mission")
        m_stats_view()
        c1, c2 = st.columns(2)
        c1.metric(T("Score"), ss.m_score)
        c2.metric(T("Rank"), T(rank_of(ss.m_score)))
        st.subheader("📋 " + T("Mission debrief"))
        for ei, ci in ss.m_hist:
            e = EVENTS[ei]
            ch = e["choices"][ci]
            best = e["choices"][0]
            icon = {100: "✅", 50: "⚠️", 0: "❌"}[ch["pts"]]
            with st.expander(f"{icon} {T(e['title'])}"):
                st.markdown(f"**{T('Your choice')}:** {T(ch['text'])}")
                st.markdown(f"**{T('Expert approach')}:** {T(best['text'])}")
                st.caption(T(best["why"]))
        cert = (
            "ASTRA MISSION TRAINER - CERTIFICATE\n"
            f"Callsign: {ss.get('callsign', 'Cadet')}\nMission: Artemis-Junior\n"
            f"Score: {ss.m_score}\nRank: {rank_of(ss.m_score)}\n"
        )
        st.download_button("📥 " + T("Download certificate"), cert, file_name="astra_certificate.txt")
        st.button("🔄 " + C("restart"), key="m_restart_end", on_click=m_reset)

# =============================================================================
# 2) MOON BASE BUILDER
# =============================================================================
with tabs[1]:
    st.subheader("🌙 " + T("Moon Base Builder"))
    st.write(T("Design a lunar base for your crew. Balance power, living space, food and water, then see if the base survives the lunar night. This is a simplified game model."))
    site = st.selectbox(T("Base location"), [T("Polar ridge (short darkness, about 2 days)"), T("Equator (14-day night)")])
    equator = site == T("Equator (14-day night)")
    bc1, bc2 = st.columns(2)
    crew_b = bc1.slider(T("Crew size"), 2, 8, 4, key="mb_crew")
    panels = bc1.slider(T("Solar panel fields"), 0, 12, 4)
    batts = bc1.slider(T("Battery banks"), 0, 12, 3)
    habs = bc2.slider(T("Habitat modules"), 1, 6, 2)
    farms = bc2.slider(T("Greenhouse modules"), 0, 6, 1)
    rovers = bc2.slider(T("Ice-mining rovers"), 0, 6, 1)

    gen = panels * 20.0
    load = crew_b * 3.0 + habs * 2.0 + farms * 10.0 + rovers * 3.0
    daylight_h = 354 if equator else 600
    dark_h = 354 if equator else 48
    stored = min(max(0.0, gen - load) * daylight_h, batts * 1000.0)
    need_night = load * dark_h
    day_ok = gen >= load
    night_ok = stored >= need_night
    space_ok = habs * 2 >= crew_b
    food_frac = min(1.0, farms * 2 / crew_b)
    water_frac = min(1.0, rovers * 2 / crew_b)
    score = (40 if day_ok else int(40 * gen / load) if load else 0)
    score += int(30 * min(1.0, stored / need_night)) if need_night else 30
    score += 10 if space_ok else int(10 * habs * 2 / crew_b)
    score += int(10 * food_frac) + int(10 * water_frac)

    bm1, bm2, bm3 = st.columns(3)
    bm1.metric(T("Power generated (kW)"), f"{gen:.0f}")
    bm2.metric(T("Power used (kW)"), f"{load:.0f}")
    bm3.metric(T("Base score"), f"{score}/100")
    st.progress(min(score / 100, 1.0))
    bar_chart(pd.DataFrame(
        {T("Value"): [gen, load]}, index=[T("Power generated (kW)"), T("Power used (kW)")]))
    st.write(("✅ " if day_ok else "❌ ") + T("Daytime power"))
    st.write(("✅ " if night_ok else "❌ ") + T("Night power from batteries"))
    st.write(("✅ " if space_ok else "❌ ") + T("Living space"))
    st.write(f"🥬 {T('Food self-sufficiency')}: {food_frac * 100:.0f}%")
    st.write(f"💧 {T('Water self-sufficiency')}: {water_frac * 100:.0f}%")
    if day_ok and night_ok and space_ok and food_frac >= 0.5 and water_frac >= 0.5:
        st.success("🌙 " + T("Your Moon base is safe and working! The crew can live there."))
        mark("base")
    else:
        st.info(T("Fix the items marked with a red X to make the base work."))

# =============================================================================
# 3) ORBIT LAB
# =============================================================================
MU = 3.986004418e14  # m^3/s^2
RE = 6371.0  # km


def orbit_chart(r_km):
    th = np.linspace(0, 2 * np.pi, 240)
    n = len(th)
    df = pd.concat([
        pd.DataFrame({"x": RE * np.cos(th), "y": RE * np.sin(th), "body": "Earth", "i": range(n)}),
        pd.DataFrame({"x": r_km * np.cos(th), "y": r_km * np.sin(th), "body": "Orbit", "i": range(n)}),
    ])
    lim = r_km * 1.1
    return (
        alt.Chart(df).mark_line(strokeWidth=3).encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[-lim, lim]), axis=None),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[-lim, lim]), axis=None),
            color=alt.Color("body:N", scale=alt.Scale(domain=["Earth", "Orbit"], range=["#4b8bff", "#ff9f43"]), legend=None),
            order="i:Q",
        ).properties(width=320, height=320)
    )


def set_alt(v):
    ss.orb_alt = v


with tabs[2]:
    st.subheader("🌍 " + T("Orbit Lab"))
    st.write(T("Higher orbits are slower and take longer. Challenge: find the altitude where a satellite stays above the same spot on Earth (a 24-hour orbit)."))
    b1, b2, b3 = st.columns(3)
    b1.button("🛰️ ISS (400 km)", on_click=set_alt, args=(400,), use_container_width=True)
    b2.button("📡 GPS (20,200 km)", on_click=set_alt, args=(20200,), use_container_width=True)
    b3.button("🎯 " + T("Try 36,000 km"), on_click=set_alt, args=(36000,), use_container_width=True)
    h = st.slider(T("Orbit altitude (km)"), 200, 45000, step=50, key="orb_alt")
    r = RE + h
    v = math.sqrt(MU / (r * 1000)) / 1000
    period_s = 2 * math.pi * math.sqrt((r * 1000) ** 3 / MU)
    o1, o2, o3 = st.columns(3)
    o1.metric(T("Orbital speed (km/s)"), f"{v:.2f}")
    o2.metric(T("Period (hours)"), f"{period_s / 3600:.2f}")
    o3.metric(T("Orbits per day"), f"{86400 / period_s:.2f}")
    left, right = st.columns([1, 1])
    with left:
        show_chart(orbit_chart(r), False)
    with right:
        hs = np.linspace(200, 45000, 120)
        per = [2 * math.pi * math.sqrt(((RE + x) * 1000) ** 3 / MU) / 3600 for x in hs]
        line_chart(pd.DataFrame({T("Period (hours)"): per}, index=hs))
        st.caption(T("Orbit period vs altitude (km)"))
    if abs(h - 35786) <= 300:
        st.success("🎯 " + T("Geostationary orbit found! The satellite orbits once every 24 hours, so it hovers over one spot."))
        mark("orbit")

# =============================================================================
# 4) GRAVITY LAB
# =============================================================================
with tabs[3]:
    st.subheader("🪐 " + T("Gravity Lab"))
    st.write(T("See how much you would weigh on other worlds and how high you could jump."))
    g1, g2 = st.columns(2)
    mass = g1.slider(T("Your mass (kg)"), 20, 120, 50)
    body = g2.selectbox(T("Choose a world"), list(BODIES), index=3, format_func=T)
    g = BODIES[body]
    w_eq = mass * g / 9.80665
    gm1, gm2, gm3 = st.columns(3)
    gm1.metric(T("Weight (newtons)"), f"{mass * g:.0f}")
    gm2.metric(T("Feels like (kg on Earth)"), f"{w_eq:.1f}")
    gm3.metric(T("Jump height (an Earth 0.5 m jump)"), f"{0.5 * 9.81 / g:.1f} m")
    df = pd.DataFrame({T("Feels like (kg on Earth)"): [mass * x / 9.80665 for x in BODIES.values()]}, index=[T(n) for n in BODIES])
    bar_chart(df)

    st.markdown("---")
    st.markdown("#### 🎂 " + T("Your age on other planets"))
    age = st.slider(T("Your age (Earth years)"), 5, 100, 14)
    adf = pd.DataFrame({T("Age (planet years)"): [round(age / y, 2) for y in YEARS.values()]}, index=[T(n) for n in YEARS])
    bar_chart(adf)

# =============================================================================
# 5) LIFE SUPPORT PLANNER
# =============================================================================
with tabs[4]:
    st.subheader("🫁 " + T("Life Support Planner"))
    st.write(T("Plan supplies for a mission. Values are approximate planning numbers per person per day."))
    l1, l2, l3 = st.columns(3)
    crew = l1.slider(T("Crew size"), 1, 8, 4)
    days = l2.slider(T("Mission length (days)"), 1, 1000, 180)
    rec = l3.slider(T("Water recycling (%)"), 0, 98, 90)
    o2 = 0.84 * crew * days
    water_total = 3.5 * crew * days
    water_launch = water_total * (1 - rec / 100)
    food = 1.8 * crew * days
    co2 = 1.0 * crew * days
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(T("Oxygen needed (kg)"), f"{o2:,.0f}")
    k2.metric(T("Water to launch (kg)"), f"{water_launch:,.0f}")
    k3.metric(T("Food (kg)"), f"{food:,.0f}")
    k4.metric(T("CO2 to remove (kg)"), f"{co2:,.0f}")
    df = pd.DataFrame({T("Mass (kg)"): [o2, water_launch, food]}, index=[T("Oxygen"), T("Water"), T("Food")])
    bar_chart(df)
    saved = water_total - water_launch
    st.info(T("Water saved by recycling (kg)") + f": {saved:,.0f}")
    st.caption(T("Recycling is why long missions like a trip to Mars need a closed-loop life support system."))

# =============================================================================
# 6) RE-ENTRY LAB
# =============================================================================
with tabs[5]:
    st.subheader("🔥 " + T("Re-entry Lab"))
    st.write(T("Choose the entry angle. Too shallow and the capsule bounces off the atmosphere. Too steep and heat and g-forces become dangerous. This is a simplified model."))
    ang = st.slider(T("Entry angle (degrees)"), 3.0, 12.0, 6.5, 0.1)
    peak_g = (ang ** 1.6) / 4.0
    temp = 2760 * math.sqrt(ang / 6.5)
    r1, r2 = st.columns(2)
    r1.metric(T("Peak g-force"), f"{peak_g:.1f} g")
    r2.metric(T("Heat shield temperature (C)"), f"{temp:,.0f}")
    xs = np.linspace(3, 12, 90)
    gdf = pd.DataFrame({"angle": xs, "g": (xs ** 1.6) / 4.0})
    band = pd.DataFrame({"a": [5.2], "b": [7.4]})
    chart = (
        alt.Chart(band).mark_rect(opacity=0.2, color="green").encode(x="a:Q", x2="b:Q")
        + alt.Chart(gdf).mark_line(color="#ff9f43").encode(x=alt.X("angle:Q", title=T("Entry angle (degrees)")), y=alt.Y("g:Q", title="g"))
        + alt.Chart(pd.DataFrame({"x": [ang]})).mark_rule(color="red").encode(x="x:Q")
    ).properties(height=260)
    show_chart(chart, True)
    st.caption(T("Green band: safe entry corridor."))
    if ang < 5.2:
        st.error("↗️ " + T("Too shallow! The capsule skips off the atmosphere and cannot return."))
    elif ang <= 7.4:
        st.success("✅ " + T("Perfect entry! The crew is safe."))
        mark("reentry")
    elif ang <= 9.5:
        st.warning("⚠️ " + T("Too steep! Very high g-force and heat. The crew is in danger."))
    else:
        st.error("💥 " + T("Far too steep! The capsule is destroyed."))

# =============================================================================
# 7) MARS LANDING (turn-based lander)
# =============================================================================
def ml_reset():
    ss.ml = {"alt": 1000.0, "v": -80.0, "fuel": 100.0, "t": 0, "hist": [(0, 1000.0)], "status": "flying"}


def ml_step():
    m = ss.ml
    if m["status"] != "flying":
        return
    b = ss.get("burn", 0) / 100
    use = b * 6
    if use > m["fuel"]:
        use = m["fuel"]
        b = use / 6
    m["fuel"] -= use
    a = -3.71 + b * 12
    v_new = m["v"] + a * 2
    alt_new = m["alt"] + (m["v"] + v_new) / 2 * 2
    m["t"] += 2
    m["v"] = v_new
    if alt_new <= 0:
        m["alt"] = 0.0
        m["status"] = "landed" if abs(v_new) <= 3 else "crashed"
    else:
        m["alt"] = alt_new
    m["hist"].append((m["t"], m["alt"]))


if "ml" not in ss:
    ml_reset()

with tabs[6]:
    st.subheader("🔴 " + T("Mars Landing"))
    st.write(T("Land softly on Mars! Each turn lasts 2 seconds. Set the engine power, then burn. Touch down slower than 3 m/s. Do not run out of fuel."))
    m = ss.ml
    q1, q2, q3 = st.columns(3)
    q1.metric(T("Altitude (m)"), f"{m['alt']:.0f}")
    q2.metric(T("Speed (m/s)"), f"{m['v']:.1f}")
    q3.metric(T("Fuel"), f"{m['fuel']:.0f}%")
    st.progress(max(0.0, min(m["fuel"] / 100, 1.0)))
    if m["status"] == "flying":
        st.slider(T("Engine power (%)"), 0, 100, 0, 10, key="burn")
        st.button("🔥 " + T("Burn for 2 seconds"), type="primary", on_click=ml_step)
    elif m["status"] == "landed":
        st.success("🎉 " + T("Touchdown! Soft landing on Mars."))
        mark("mars")
    else:
        st.error("💥 " + T("Crash! You hit the surface too fast."))
    hdf = pd.DataFrame(m["hist"], columns=["t", "alt"]).set_index("t")
    line_chart(hdf)
    st.button("🔄 " + C("restart"), key="ml_restart", on_click=ml_reset)

# =============================================================================
# 8) EXOPLANET LAB
# =============================================================================
with tabs[7]:
    st.subheader("🔭 " + T("Exoplanet Lab"))
    st.write(T("Find planets where liquid water could exist. Pick a star and place your planet. The green band is the habitable zone: not too hot and not too cold. This is a simplified model."))
    star_name = st.selectbox(T("Star type"), list(STARS), index=1, format_func=T)
    lum = STARS[star_name]
    ex1, ex2 = st.columns(2)
    dist = ex1.slider(T("Planet distance from its star (AU)"), 0.05, 6.0, 1.0, 0.01)
    albedo = ex2.slider(T("Reflectivity (albedo)"), 0.0, 0.9, 0.3, 0.05)
    hz_in, hz_out = 0.95 * math.sqrt(lum), 1.37 * math.sqrt(lum)
    t_eq = 278.6 * ((1 - albedo) ** 0.25) * (lum ** 0.25) / math.sqrt(dist)
    em1, em2, em3 = st.columns(3)
    em1.metric(T("Equilibrium temperature (C)"), f"{t_eq - 273.15:.0f}")
    em2.metric(T("Habitable zone starts (AU)"), f"{hz_in:.2f}")
    em3.metric(T("Habitable zone ends (AU)"), f"{hz_out:.2f}")
    xs_ = alt.Scale(domain=[0, 6])
    chart = alt.Chart(pd.DataFrame({"a": [hz_in], "b": [hz_out]})).mark_rect(opacity=0.25, color="green").encode(
        x=alt.X("a:Q", scale=xs_, title="AU"), x2="b:Q")
    chart += alt.Chart(pd.DataFrame({"x": [dist], "y": [0.0]})).mark_point(size=260, filled=True, color="#ffd36e").encode(
        x=alt.X("x:Q", scale=xs_), y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-1, 1])))
    if star_name == "Sun-like star":
        sol = pd.DataFrame({"x": [0.39, 0.72, 1.0, 1.52, 5.2], "y": [0.0] * 5,
                            "name": [T(n) for n in ("Mercury", "Venus", "Earth", "Mars", "Jupiter")]})
        chart += alt.Chart(sol).mark_point(size=60, color="#9bb7ff").encode(x=alt.X("x:Q", scale=xs_), y=alt.Y("y:Q", axis=None))
        chart += alt.Chart(sol).mark_text(dy=-16, color="#ffffff").encode(x=alt.X("x:Q", scale=xs_), y=alt.Y("y:Q", axis=None), text="name:N")
    show_chart(chart.properties(height=220), True)
    if hz_in <= dist <= hz_out:
        st.success("🌱 " + T("In the habitable zone! Liquid water could exist here."))
        mark("exo")
    elif dist < hz_in:
        st.error("🔥 " + T("Too hot. Water would boil away."))
    else:
        st.info("🧊 " + T("Too cold. Water would freeze."))
    st.caption(T("Earth's equilibrium temperature is about -18 C. Its atmosphere warms it to about 15 C."))

# =============================================================================
# 9) PLANETARY DEFENSE
# =============================================================================
with tabs[8]:
    st.subheader("☄️ " + T("Planetary Defense"))
    st.write(T("An asteroid is heading for Earth! Hit it with kinetic impactors, like NASA's DART mission, early enough to push it off course. This is a simplified model."))
    pd1, pd2 = st.columns(2)
    dia = pd1.slider(T("Asteroid diameter (m)"), 50, 600, 160, 10)
    lead = pd1.slider(T("Warning time (years)"), 0.5, 20.0, 8.0, 0.5)
    n_imp = pd2.slider(T("Number of impactor spacecraft"), 1, 20, 4)
    m_imp = pd2.slider(T("Spacecraft mass (kg)"), 300, 1500, 600, 50)
    v_imp = pd2.slider(T("Impact speed (km/s)"), 4.0, 10.0, 6.0, 0.5)
    BETA = 3.0
    ast_mass = 2000.0 * (4.0 / 3.0) * math.pi * (dia / 2.0) ** 3
    dv = BETA * n_imp * m_imp * v_imp * 1000.0 / ast_mass
    YR = 3.15576e7
    shift_km = dv * lead * YR / 1000.0
    NEED_KM = 6371.0
    dm1, dm2, dm3 = st.columns(3)
    dm1.metric(T("Asteroid mass (million tonnes)"), f"{ast_mass / 1e9:.1f}")
    dm2.metric(T("Speed change (mm/s)"), f"{dv * 1000:.2f}")
    dm3.metric(T("Miss distance (km)"), f"{shift_km:,.0f}")
    st.progress(min(shift_km / NEED_KM, 1.0))
    leads = np.linspace(0.5, 20, 40)
    ldf = pd.DataFrame({"years": leads, "km": [dv * y * YR / 1000.0 for y in leads]})
    dchart = alt.Chart(ldf).mark_line(color="#ff9f43").encode(
        x=alt.X("years:Q", title=T("Warning time (years)")), y=alt.Y("km:Q", title="km"))
    dchart += alt.Chart(pd.DataFrame({"km": [NEED_KM]})).mark_rule(color="red").encode(y="km:Q")
    show_chart(dchart.properties(height=240), True)
    st.caption(T("Red line: about one Earth radius (6,371 km), enough to miss Earth."))
    if shift_km >= NEED_KM:
        st.success("🛡️ " + T("Earth is safe! The asteroid will miss us."))
        mark("defense")
    else:
        st.warning("⚠️ " + T("Not enough deflection. Add spacecraft, mass, speed or warning time."))
    st.caption(T("In 2022 NASA's DART spacecraft hit the asteroid Dimorphos and shortened its orbit by about 32 minutes."))

# =============================================================================
# 10) MOON PHASE LAB
# =============================================================================
def phase_name(d):
    for lim, nm in [(1.0, "New Moon"), (6.4, "Waxing Crescent"), (8.4, "First Quarter"), (13.4, "Waxing Gibbous"),
                    (16.1, "Full Moon"), (21.1, "Waning Gibbous"), (23.1, "Last Quarter"), (28.5, "Waning Crescent")]:
        if d < lim:
            return nm
    return "New Moon"


def moon_svg(day):
    th = 2 * math.pi * day / 29.53
    if th <= math.pi:
        sign, k = 1, math.cos(th)
    else:
        sign, k = -1, math.cos(2 * math.pi - th)
    r = 80
    pts = []
    for i in range(61):
        phi = math.pi * i / 60
        pts.append((sign * r * math.sin(phi), -r * math.cos(phi)))
    for i in range(60, -1, -1):
        phi = math.pi * i / 60
        pts.append((sign * k * r * math.sin(phi), -r * math.cos(phi)))
    poly = " ".join(f"{100 + x:.1f},{100 + y:.1f}" for x, y in pts)
    return (f'<svg width="220" height="220" viewBox="0 0 200 200"><circle cx="100" cy="100" r="80" fill="#171c3a" '
            f'stroke="#5a6aa8" stroke-width="2"/><polygon points="{poly}" fill="#f1eedf"/></svg>')


with tabs[9]:
    st.subheader("🌗 " + T("Moon Phase Lab"))
    st.write(T("Slide through one lunar month and watch the Moon change. The Moon takes about 29.5 days to go from new moon to new moon."))
    day = st.slider(T("Days since new moon"), 0.0, 29.5, 7.4, 0.1)
    illum = (1 - math.cos(2 * math.pi * day / 29.53)) / 2
    mc1, mc2 = st.columns([1, 1])
    with mc1:
        st.markdown(f'<div style="text-align:center">{moon_svg(day)}</div>', unsafe_allow_html=True)
    with mc2:
        st.metric(T("Phase"), T(phase_name(day)))
        st.metric(T("Illuminated"), f"{illum * 100:.0f}%")
        st.metric(T("Moon age (days)"), f"{day:.1f}")
    st.caption(T("The Moon always shows the same face to Earth because it is tidally locked."))

st.divider()
st.caption(T("Independent educational project created for the NASA Space Apps Challenge. Not affiliated with or endorsed by NASA. Scenarios and models are simplified and fictional."))

