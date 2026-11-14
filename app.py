import random
import streamlit as st

st.set_page_config(page_title="ASTRA MISSION TRAINER", page_icon="🚀", layout="wide")

# ----------------------------------------------------------------------------
# STYLE
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .hero {padding: 1.2rem 1.4rem; border-radius: 16px;
           background: linear-gradient(135deg,#0b1026 0%,#1b2a6b 55%,#4b2a7b 100%);
           color: #fff; margin-bottom: 1rem;}
    .hero h1 {margin: 0; font-size: 1.9rem; letter-spacing: 2px;}
    .hero p {margin: .3rem 0 0 0; opacity: .85;}
    .event {padding: 1rem 1.2rem; border-left: 5px solid #ff4b4b;
            background: rgba(255,75,75,.08); border-radius: 8px; margin: .6rem 0;}
    .fact {padding: .7rem 1rem; border-left: 5px solid #4b8bff;
           background: rgba(75,139,255,.08); border-radius: 8px; margin: .6rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# TEXTS
# ----------------------------------------------------------------------------
UI = {
    "tagline": {
        "tr": "Genç astronotlar için görev simülasyonu ve acil durum karar eğitimi",
        "en": "Mission simulation and emergency decision training for young astronauts",
    },
    "tab_mission": {"tr": "🛰️ Görev Simülasyonu", "en": "🛰️ Mission Simulator"},
    "tab_academy": {"tr": "🎓 Uzay Akademisi", "en": "🎓 Space Academy"},
    "tab_about": {"tr": "ℹ️ Proje Hakkında", "en": "ℹ️ About"},
    "language": {"tr": "Dil / Language", "en": "Language / Dil"},
    "reset": {"tr": "🔄 Baştan başla", "en": "🔄 Restart"},
    "callsign": {"tr": "Çağrı adın (callsign)", "en": "Your callsign"},
    "start": {"tr": "🚀 Göreve başla", "en": "🚀 Launch mission"},
    "intro": {
        "tr": "Artemis-Junior görevindesin. Ay yörüngesinden Dünya'ya dönüş yolculuğunda 6 acil durum seni bekliyor. Oksijen ve enerji sıfıra inerse görev başarısız olur. Her kararın sonucu bir sonrakini etkiler.",
        "en": "You are on the Artemis-Junior mission. On the return trip from lunar orbit, 6 emergencies are waiting. If oxygen or power reaches zero, the mission fails. Every decision affects the next one.",
    },
    "oxygen": {"tr": "Oksijen", "en": "Oxygen"},
    "power": {"tr": "Enerji", "en": "Power"},
    "fuel": {"tr": "Yakıt", "en": "Fuel"},
    "morale": {"tr": "Moral", "en": "Morale"},
    "event": {"tr": "Olay", "en": "Event"},
    "decide": {"tr": "Kararını ver:", "en": "Make your decision:"},
    "result": {"tr": "Sonuç", "en": "Result"},
    "next": {"tr": "➡️ Sonraki olay", "en": "➡️ Next event"},
    "finish": {"tr": "📋 Görev raporunu gör", "en": "📋 See mission debrief"},
    "score": {"tr": "Puan", "en": "Score"},
    "rank": {"tr": "Rütbe", "en": "Rank"},
    "success": {"tr": "🎉 GÖREV TAMAMLANDI! Mürettebat güvenle Dünya'ya döndü.", "en": "🎉 MISSION COMPLETE! The crew returned safely to Earth."},
    "fail": {"tr": "💥 GÖREV BAŞARISIZ. Kritik sistemler çöktü.", "en": "💥 MISSION FAILED. Critical systems collapsed."},
    "debrief": {"tr": "📋 Görev Değerlendirmesi (Debrief)", "en": "📋 Mission Debrief"},
    "your_choice": {"tr": "Senin seçimin", "en": "Your choice"},
    "expert": {"tr": "Uzman yaklaşımı", "en": "Expert approach"},
    "cert": {"tr": "📥 Sertifikayı indir", "en": "📥 Download certificate"},
    "quiz_title": {"tr": "Uzay bilgini test et", "en": "Test your space knowledge"},
    "quiz_check": {"tr": "Cevapları kontrol et", "en": "Check answers"},
    "quiz_result": {"tr": "Doğru sayın", "en": "Correct answers"},
    "quiz_pick": {"tr": "Bir seçenek seç", "en": "Pick an option"},
    "correct": {"tr": "Doğru ✅", "en": "Correct ✅"},
    "wrong": {"tr": "Yanlış ❌ Doğru cevap", "en": "Wrong ❌ Correct answer"},
}

EVENTS = [
    {
        "title": {"tr": "Oksijen sızıntısı", "en": "Oxygen leak"},
        "story": {
            "tr": "Alarm çalıyor! Yaşam modülünde oksijen basıncı hızla düşüyor.",
            "en": "Alarm! Oxygen pressure in the habitat module is dropping fast.",
        },
        "fact": {
            "tr": "1970'te Apollo 13'te bir oksijen tankı hasar gördü. Mürettebat, Ay modülünü cankurtaran botu gibi kullanarak güvenle döndü.",
            "en": "In 1970 an oxygen tank failed on Apollo 13. The crew used the lunar module as a lifeboat and returned safely.",
        },
        "choices": [
            {
                "text": {"tr": "Sızan modülü izole et, kapağı kapat ve yama kitiyle sızıntıyı kapat", "en": "Isolate the leaking module, close the hatch and seal the leak with the patch kit"},
                "fx": {"o": -5, "m": 5}, "pts": 100,
                "why": {"tr": "Sorunu izole etmek kaybı sınırlar ve diğer modülleri korur.", "en": "Isolating the problem limits the loss and protects other modules."},
            },
            {
                "text": {"tr": "Yedek tanklardan oksijen akışını artır ve izle", "en": "Increase oxygen flow from reserve tanks and monitor"},
                "fx": {"o": -20}, "pts": 50,
                "why": {"tr": "Geçici işe yarar ama sızıntı sürdüğü için yedek hızla tükenir.", "en": "It helps temporarily, but the leak continues and reserves drain quickly."},
            },
            {
                "text": {"tr": "Alarmı görmezden gel, muhtemelen sensör hatasıdır", "en": "Ignore the alarm, it is probably a sensor error"},
                "fx": {"o": -40, "m": -10}, "pts": 0,
                "why": {"tr": "Alarmlar asla varsayımla kapatılmaz; önce doğrulanır.", "en": "Alarms are never dismissed by assumption; they are verified first."},
            },
        ],
    },
    {
        "title": {"tr": "Enerji kaybı", "en": "Power loss"},
        "story": {
            "tr": "Güneş panellerinden biri yönünü kaybetti ve enerji üretimi düştü.",
            "en": "One solar array lost its orientation and power generation dropped.",
        },
        "fact": {
            "tr": "Uluslararası Uzay İstasyonu enerjisini büyük güneş panellerinden alır; kritik olmayan sistemler gerekirse kapatılır.",
            "en": "The International Space Station gets its power from large solar arrays; non-critical systems are shut down when needed.",
        },
        "choices": [
            {
                "text": {"tr": "Yalnızca kritik sistemlere enerji ver, diğerlerini kapat", "en": "Switch to essential-only power and shut down non-critical systems"},
                "fx": {"p": -5}, "pts": 100,
                "why": {"tr": "Önce yaşam destek ve iletişim: enerji öncelik sırasına göre dağıtılır.", "en": "Life support and communications come first: power is rationed by priority."},
            },
            {
                "text": {"tr": "Sadece laboratuvarı kapat", "en": "Shut down only the lab"},
                "fx": {"p": -15}, "pts": 50,
                "why": {"tr": "Biraz tasarruf sağlar ama yeterli değil.", "en": "It saves some power but not enough."},
            },
            {
                "text": {"tr": "Tüm sistemleri aynı anda yeniden başlat", "en": "Restart all systems at once"},
                "fx": {"p": -35, "m": -5}, "pts": 0,
                "why": {"tr": "Yeniden başlatma ani enerji çekişi yaratır ve durumu kötüleştirir.", "en": "Restarting causes a power surge and makes things worse."},
            },
        ],
    },
    {
        "title": {"tr": "İletişim kesintisi", "en": "Communication blackout"},
        "story": {
            "tr": "Görev Kontrol ile bağlantı koptu. Radyodan sadece parazit geliyor.",
            "en": "Contact with Mission Control is lost. Only static on the radio.",
        },
        "fact": {
            "tr": "Ay'ın arkasından geçerken uzay araçlarının Dünya ile iletişimi planlı olarak kesilir; bunun için önceden hazırlanmış prosedürler vardır.",
            "en": "When passing behind the Moon, spacecraft planned lose contact with Earth; there are prepared procedures for this.",
        },
        "choices": [
            {
                "text": {"tr": "Kayıp-iletişim prosedürünü uygula, yedek antene geç, planlı aralıklarla tekrar dene", "en": "Follow the lost-comm checklist, switch to the backup antenna, retry at scheduled intervals"},
                "fx": {"p": -5}, "pts": 100,
                "why": {"tr": "Sakin kalıp prosedürü izlemek en güvenli yoldur.", "en": "Staying calm and following the procedure is the safest path."},
            },
            {
                "text": {"tr": "Bir şey yapmadan bekle", "en": "Wait without doing anything"},
                "fx": {"m": -10}, "pts": 50,
                "why": {"tr": "Beklemek tek başına yeterli değil; yedek seçenekleri denemek gerekir.", "en": "Waiting alone is not enough; backup options must be tried."},
            },
            {
                "text": {"tr": "Konumu 'düzeltmek' için plansız motor ateşlemesi yap", "en": "Do an unplanned engine burn to 'fix' the position"},
                "fx": {"f": -30, "m": -5}, "pts": 0,
                "why": {"tr": "Yer kontrolü olmadan manevra yakıtı boşa harcar ve yörüngeyi bozabilir.", "en": "Maneuvering without ground control wastes fuel and can disturb the orbit."},
            },
        ],
    },
    {
        "title": {"tr": "Kabinde yangın alarmı", "en": "Cabin fire alarm"},
        "story": {
            "tr": "Ekipman rafından duman çıkıyor ve yangın alarmı çalıyor.",
            "en": "Smoke is coming from an equipment rack and the fire alarm is sounding.",
        },
        "fact": {
            "tr": "Uzay istasyonlarında yangınla mücadele için maskeler ve CO2 söndürücüler bulunur.",
            "en": "Space stations carry masks and CO2 extinguishers for fire emergencies.",
        },
        "choices": [
            {
                "text": {"tr": "Etkilenen ekipmanın enerjisini kes, maskeleri tak, CO2 söndürücü kullan", "en": "Cut power to the affected equipment, put on masks, use the CO2 extinguisher"},
                "fx": {"o": -5, "p": -10}, "pts": 100,
                "why": {"tr": "Enerjiyi kesmek yangının kaynağını durdurur; maske dumandan korur.", "en": "Cutting power stops the fire source; masks protect from smoke."},
            },
            {
                "text": {"tr": "Söndürücü kullan ama ekipman açık kalsın", "en": "Use the extinguisher but keep the equipment powered"},
                "fx": {"o": -10, "p": -15}, "pts": 50,
                "why": {"tr": "Enerji açıkken yangın yeniden başlayabilir.", "en": "With power on, the fire can restart."},
            },
            {
                "text": {"tr": "Dumanı atmak için havalandırmayı uzaya aç", "en": "Open the vent to space to remove the smoke"},
                "fx": {"o": -35, "m": -10}, "pts": 0,
                "why": {"tr": "Kabin havasını uzaya vermek mürettebatı tehlikeye atar.", "en": "Venting cabin air to space endangers the crew."},
            },
        ],
    },
    {
        "title": {"tr": "Mürettebat sağlığı", "en": "Crew health"},
        "story": {
            "tr": "Bir mürettebat üyesi başı dönüyor ve mide bulantısı yaşıyor.",
            "en": "A crew member feels dizzy and nauseous.",
        },
        "fact": {
            "tr": "Birçok astronot, ağırlıksızlığa uyum sürecinde ilk günlerde uzay tutması yaşayabilir.",
            "en": "Many astronauts experience space motion sickness while adapting to weightlessness in the first days.",
        },
        "choices": [
            {
                "text": {"tr": "Dinlenmesini sağla, su içir ve telsizle uçuş doktoruna danış", "en": "Let them rest, hydrate, and consult the flight surgeon by radio"},
                "fx": {"m": 10}, "pts": 100,
                "why": {"tr": "Dinlenme ve tıbbi destek sağlığı korur, ekip moralini yükseltir.", "en": "Rest and medical support protect health and raise crew morale."},
            },
            {
                "text": {"tr": "Zor bir görev verip dikkatini dağıt", "en": "Give them a tough task to distract them"},
                "fx": {"m": -10}, "pts": 50,
                "why": {"tr": "Zorlamak durumu kötüleştirebilir.", "en": "Pushing them can make it worse."},
            },
            {
                "text": {"tr": "Görmezden gel ve programa devam et", "en": "Ignore it and keep the schedule"},
                "fx": {"m": -25}, "pts": 0,
                "why": {"tr": "Mürettebat sağlığı görevin parçasıdır; belirtiler ciddiye alınır.", "en": "Crew health is part of the mission; symptoms are taken seriously."},
            },
        ],
    },
    {
        "title": {"tr": "Dünya'ya giriş hazırlığı", "en": "Re-entry preparation"},
        "story": {
            "tr": "Dünya atmosferine giriş yaklaşıyor. Isı kalkanı ve yakıt durumunu kontrol etmen gerekiyor.",
            "en": "Atmospheric re-entry is approaching. You must check the heat shield and fuel status.",
        },
        "fact": {
            "tr": "Atmosfere girişte kapsül çok yüksek sıcaklıklara ulaşır; ısı kalkanı mürettebatı korur.",
            "en": "During re-entry the capsule reaches extremely high temperatures; the heat shield protects the crew.",
        },
        "choices": [
            {
                "text": {"tr": "Görev Kontrol ile tüm kontrol listesini uygula, ısı kalkanı ve yakıtı doğrula", "en": "Run the full checklist with Mission Control, verify heat shield and fuel"},
                "fx": {"f": -10, "m": 5}, "pts": 100,
                "why": {"tr": "Kontrol listeleri hata payını azaltır; kritik aşamada atlama yapılmaz.", "en": "Checklists reduce error; nothing is skipped at a critical stage."},
            },
            {
                "text": {"tr": "Zaman kazanmak için iki maddeyi atla", "en": "Skip two items to save time"},
                "fx": {"f": -5, "m": -5}, "pts": 50,
                "why": {"tr": "Küçük atlamalar büyük risklere dönüşebilir.", "en": "Small skips can turn into big risks."},
            },
            {
                "text": {"tr": "Doğrulama yapmadan hemen girişe başla", "en": "Start re-entry immediately without verification"},
                "fx": {"p": -20, "f": -20}, "pts": 0,
                "why": {"tr": "Doğrulanmamış bir girişte hata geri alınamaz.", "en": "In an unverified re-entry, mistakes cannot be undone."},
            },
        ],
    },
]

QUIZ = [
    {
        "q": {"tr": "Uzaya çıkan ilk insan kimdir?", "en": "Who was the first human in space?"},
        "o": {"tr": ["Neil Armstrong", "Yuri Gagarin", "Buzz Aldrin"], "en": ["Neil Armstrong", "Yuri Gagarin", "Buzz Aldrin"]},
        "a": 1,
    },
    {
        "q": {"tr": "Ay'ın yerçekimi Dünya'nınkinin yaklaşık kaçta kaçıdır?", "en": "The Moon's gravity is about what fraction of Earth's?"},
        "o": {"tr": ["Yaklaşık 1/2", "Yaklaşık 1/6", "Aynı"], "en": ["About 1/2", "About 1/6", "The same"]},
        "a": 1,
    },
    {
        "q": {"tr": "Uluslararası Uzay İstasyonu yaklaşık kaç km yükseklikte döner?", "en": "At roughly what altitude does the ISS orbit?"},
        "o": {"tr": ["40 km", "4.000 km", "400 km"], "en": ["40 km", "4,000 km", "400 km"]},
        "a": 2,
    },
    {
        "q": {"tr": "Güneş ışığı Dünya'ya yaklaşık ne kadar sürede ulaşır?", "en": "How long does sunlight take to reach Earth?"},
        "o": {"tr": ["Yaklaşık 8 dakika", "Yaklaşık 8 saat", "Yaklaşık 8 saniye"], "en": ["About 8 minutes", "About 8 hours", "About 8 seconds"]},
        "a": 0,
    },
    {
        "q": {"tr": "ISS'teki astronotlar neden ağırlıksız hisseder?", "en": "Why do astronauts on the ISS feel weightless?"},
        "o": {
            "tr": ["O yükseklikte yerçekimi yoktur", "Dünya etrafında sürekli serbest düşüş halindedirler", "İstasyon atmosferin dışındadır"],
            "en": ["There is no gravity at that altitude", "They are in constant free fall around Earth", "The station is outside the atmosphere"],
        },
        "a": 1,
    },
]

RANKS = [
    (500, {"tr": "Komutan 🥇", "en": "Commander 🥇"}),
    (350, {"tr": "Pilot 🥈", "en": "Pilot 🥈"}),
    (200, {"tr": "Kadet 🥉", "en": "Cadet 🥉"}),
    (0, {"tr": "Stajyer 🚀", "en": "Trainee 🚀"}),
]

# ----------------------------------------------------------------------------
# STATE
# ----------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("lang", "tr")


def reset_game():
    ss.started = False
    ss.step = 0
    ss.stats = {"o": 100, "p": 100, "f": 100, "m": 100}
    ss.score = 0
    ss.history = []
    ss.phase = "choose"
    ss.failed = False
    ss.order = [0, 1, 2]
    ss.last = None


if "started" not in ss:
    reset_game()


def tx(d):
    return d[ss.lang] if isinstance(d, dict) else d


def new_order():
    order = [0, 1, 2]
    random.shuffle(order)
    ss.order = order


def start_game():
    ss.started = True
    ss.step = 0
    new_order()


def choose(idx):
    ch = EVENTS[ss.step]["choices"][idx]
    for k, v in ch["fx"].items():
        ss.stats[k] = max(0, min(100, ss.stats[k] + v))
    ss.score += ch["pts"]
    ss.history.append({"step": ss.step, "idx": idx})
    ss.last = idx
    ss.phase = "feedback"
    if ss.stats["o"] <= 0 or ss.stats["p"] <= 0:
        ss.failed = True


def next_event():
    ss.step += 1
    if ss.failed or ss.step >= len(EVENTS):
        ss.phase = "end"
    else:
        ss.phase = "choose"
        new_order()


def rank_of(score):
    for threshold, name in RANKS:
        if score >= threshold:
            return tx(name)
    return tx(RANKS[-1][1])


def show_stats():
    cols = st.columns(4)
    items = [("o", "🫁", "oxygen"), ("p", "⚡", "power"), ("f", "⛽", "fuel"), ("m", "😊", "morale")]
    for col, (key, icon, name) in zip(cols, items):
        with col:
            st.metric(f"{icon} {tx(UI[name])}", f"{ss.stats[key]}%")
            st.progress(ss.stats[key] / 100)


# ----------------------------------------------------------------------------
# SIDEBAR + HEADER
# ----------------------------------------------------------------------------
with st.sidebar:
    lang_choice = st.radio(
        UI["language"][ss.lang],
        ["tr", "en"],
        index=0 if ss.lang == "tr" else 1,
        format_func=lambda x: "Türkçe" if x == "tr" else "English",
        horizontal=True,
    )
    if lang_choice != ss.lang:
        ss.lang = lang_choice
        st.rerun()
    if st.button(tx(UI["reset"])):
        reset_game()
        st.rerun()

st.markdown(
    f"""
    <div class="hero">
      <h1>🚀 ASTRA MISSION TRAINER</h1>
      <p>{tx(UI['tagline'])}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_mission, tab_academy, tab_about = st.tabs(
    [tx(UI["tab_mission"]), tx(UI["tab_academy"]), tx(UI["tab_about"])]
)

# ----------------------------------------------------------------------------
# MISSION TAB
# ----------------------------------------------------------------------------
with tab_mission:
    if not ss.started:
        st.info(tx(UI["intro"]))
        ss.callsign = st.text_input(tx(UI["callsign"]), value=ss.get("callsign", "Cadet"))
        st.button(tx(UI["start"]), type="primary", on_click=start_game)

    elif ss.phase in ("choose", "feedback"):
        ev = EVENTS[ss.step]
        st.caption(f"{tx(UI['event'])} {ss.step + 1}/{len(EVENTS)}  •  {tx(UI['score'])}: {ss.score}")
        show_stats()
        st.markdown(
            f'<div class="event"><b>⚠️ {tx(ev["title"])}</b><br>{tx(ev["story"])}</div>',
            unsafe_allow_html=True,
        )

        if ss.phase == "choose":
            st.subheader(tx(UI["decide"]))
            for idx in ss.order:
                st.button(
                    tx(ev["choices"][idx]["text"]),
                    key=f"choice_{ss.step}_{idx}",
                    on_click=choose,
                    args=(idx,),
                    use_container_width=True,
                )
        else:
            ch = ev["choices"][ss.last]
            icon = {100: "✅", 50: "⚠️", 0: "❌"}[ch["pts"]]
            box = {100: st.success, 50: st.warning, 0: st.error}[ch["pts"]]
            box(f"{icon} **{tx(UI['result'])}:** {tx(ch['why'])}  (+{ch['pts']})")
            st.markdown(
                f'<div class="fact">🔭 {tx(ev["fact"])}</div>',
                unsafe_allow_html=True,
            )
            last = ss.step >= len(EVENTS) - 1 or ss.failed
            st.button(
                tx(UI["finish"]) if last else tx(UI["next"]),
                type="primary",
                on_click=next_event,
            )

    else:  # end
        if ss.failed:
            st.error(tx(UI["fail"]))
        else:
            st.success(tx(UI["success"]))
            st.balloons()

        show_stats()
        c1, c2 = st.columns(2)
        c1.metric(tx(UI["score"]), ss.score)
        c2.metric(tx(UI["rank"]), rank_of(ss.score))

        st.subheader(tx(UI["debrief"]))
        for h in ss.history:
            ev = EVENTS[h["step"]]
            ch = ev["choices"][h["idx"]]
            best = next(c for c in ev["choices"] if c["pts"] == 100)
            icon = {100: "✅", 50: "⚠️", 0: "❌"}[ch["pts"]]
            with st.expander(f"{icon} {tx(ev['title'])}"):
                st.markdown(f"**{tx(UI['your_choice'])}:** {tx(ch['text'])}")
                st.markdown(f"**{tx(UI['expert'])}:** {tx(best['text'])}")
                st.caption(tx(best["why"]))

        name = ss.get("callsign", "Cadet")
        cert = (
            "ASTRA MISSION TRAINER - CERTIFICATE\n"
            f"Callsign: {name}\n"
            f"Mission: Artemis-Junior\n"
            f"Score: {ss.score}\n"
            f"Rank: {rank_of(ss.score)}\n"
        )
        st.download_button(tx(UI["cert"]), cert, file_name="astra_certificate.txt")
        st.button(tx(UI["reset"]), key="restart_end", on_click=reset_game)

# ----------------------------------------------------------------------------
# ACADEMY TAB
# ----------------------------------------------------------------------------
with tab_academy:
    st.subheader(tx(UI["quiz_title"]))
    answers = []
    for i, q in enumerate(QUIZ):
        opts = tx(q["o"])
        answers.append(st.radio(tx(q["q"]), opts, index=None, key=f"quiz_{i}_{ss.lang}"))

    if st.button(tx(UI["quiz_check"])):
        correct = 0
        for q, a in zip(QUIZ, answers):
            opts = tx(q["o"])
            right = opts[q["a"]]
            if a == right:
                correct += 1
                st.success(f"{tx(q['q'])} → {tx(UI['correct'])}")
            elif a is None:
                st.info(f"{tx(q['q'])} → {tx(UI['quiz_pick'])}")
            else:
                st.error(f"{tx(q['q'])} → {tx(UI['wrong'])}: {right}")
        st.metric(tx(UI["quiz_result"]), f"{correct}/{len(QUIZ)}")

# ----------------------------------------------------------------------------
# ABOUT TAB
# ----------------------------------------------------------------------------
with tab_about:
    if ss.lang == "tr":
        st.markdown(
            """
**ASTRA MISSION TRAINER**, NASA Space Apps Challenge "Junior Astronaut Mission Trainer" için geliştirildi.

**Amaç:** Gençlerin astronotluk, uzay bilimi, görev simülasyonu ve acil durumlarda karar verme becerilerini eğlenceli bir şekilde geliştirmesi.

**Nasıl çalışır?**
- Dallanan acil durum senaryoları: her karar oksijen, enerji, yakıt ve morali etkiler.
- Görev sonunda debrief: ne yaptın, uzman ne yapardı.
- Uzay Akademisi: kısa quiz.
- Türkçe ve İngilizce arayüz.

**Kaynaklar:** NASA'nın herkese açık bilgileri (Apollo 13, ISS, atmosfere giriş prosedürleri) eğitim amaçlı sadeleştirilerek kullanılmıştır. Senaryolar kurgusaldır ve gerçek görev prosedürlerinin yerine geçmez.
            """
        )
    else:
        st.markdown(
            """
**ASTRA MISSION TRAINER** was built for the NASA Space Apps Challenge "Junior Astronaut Mission Trainer".

**Goal:** Help young people build skills in astronaut training, space science, mission simulation and emergency decision-making in a fun way.

**How it works:**
- Branching emergency scenarios: every decision affects oxygen, power, fuel and morale.
- End-of-mission debrief: what you did and what an expert would do.
- Space Academy: a short quiz.
- Turkish and English interface.

**Sources:** Public NASA information (Apollo 13, ISS, re-entry procedures) simplified for education. Scenarios are fictional and do not replace real mission procedures.
            """
        )
