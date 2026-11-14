import streamlit as st
import random

st.set_page_config(
    page_title="ASTRA Mission Trainer",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 ASTRA MISSION TRAINER")
st.subheader("Junior Astronaut Training & Mission Simulation")

st.info("Train. Explore. Discover. Prepare for Space.")

menu = st.sidebar.radio(
    "MISSION CONTROL",
    [
        "Home",
        "Astronaut Academy",
        "Mission Simulator",
        "Gravity Laboratory",
        "Knowledge Test",
        "Emergency Training",
        "NASA Resources"
    ]
)

if menu == "Home":
    st.header("Welcome, Future Astronaut!")
    st.write("""
    ASTRA is an educational space mission training platform
    designed to introduce young learners to astronaut life,
    scientific thinking and space exploration.
    """)
    col1, col2, col3 = st.columns(3)
    col1.metric("Training Modules", "5")
    col2.metric("Mission Status", "READY")
    col3.metric("Platform", "Educational")

    st.subheader("Your Mission")
    st.write("Explore space science and prepare for your first mission.")

elif menu == "Astronaut Academy":
    st.header("👩‍🚀 Astronaut Academy")
    lessons = {
        "Microgravity": "In microgravity, objects appear to float because they and their surroundings are in continuous free fall.",
        "Space Nutrition": "Astronauts need balanced meals that provide energy and essential nutrients.",
        "Space Communication": "Astronauts communicate with mission control using radio systems.",
        "Space Suits": "Spacesuits provide oxygen, temperature regulation and protection.",
        "Spacecraft": "Spacecraft transport astronauts and equipment beyond Earth."
    }
    topic = st.selectbox("Choose a lesson", list(lessons.keys()))
    st.write(lessons[topic])

elif menu == "Mission Simulator":
    st.header("🪐 Mission Simulator")
    destination = st.selectbox(
        "Select your destination",
        ["International Space Station", "Moon", "Mars"]
    )
    mission = st.selectbox(
        "Mission objective",
        ["Scientific Research", "Observation", "Exploration"]
    )
    if st.button("START MISSION"):
        st.success("Mission simulation initiated!")
        st.write("Destination:", destination)
        st.write("Objective:", mission)
        st.write("Mission status: SIMULATION ACTIVE")

elif menu == "Gravity Laboratory":
    st.header("🌍 Gravity Laboratory")
    weight = st.number_input("Your Earth weight (kg)", min_value=1.0, value=50.0)
    gravity = {
        "Earth": 9.81,
        "Moon": 1.62,
        "Mars": 3.71,
        "Jupiter": 24.79
    }
    planet = st.selectbox("Choose a celestial body", list(gravity.keys()))
    result = weight * gravity[planet] / 9.81
    st.metric("Calculated weight", f"{result:.2f} kg")
    st.caption("Educational comparison using surface gravitational acceleration.")

elif menu == "Knowledge Test":
    st.header("🧠 Astronaut Knowledge Test")
    questions = [
        ("Which planet is known as the Red Planet?", ["Venus", "Mars", "Jupiter"], "Mars"),
        ("What does ISS stand for?", ["International Space Station", "Interstellar Space System", "International Solar Station"], "International Space Station"),
        ("Which star is closest to Earth?", ["Sirius", "The Sun", "Polaris"], "The Sun"),
        ("What do astronauts wear outside spacecraft?", ["Spacesuit", "Diving suit", "Flight jacket"], "Spacesuit"),
        ("Which force keeps planets in orbit?", ["Friction", "Gravity", "Magnetism"], "Gravity")
    ]

    score = 0
    answers = []
    for i, (q, options, correct) in enumerate(questions):
        answer = st.radio(q, options, key=f"q{i}")
        answers.append((answer, correct))

    if st.button("SUBMIT TEST"):
        score = sum(a == c for a, c in answers)
        st.success(f"Your score: {score}/{len(questions)}")
        if score == 5:
            st.balloons()
            st.success("Excellent! Astronaut knowledge confirmed.")

elif menu == "Emergency Training":
    st.header("⚠️ Emergency Decision Training")
    scenario = st.selectbox(
        "Training scenario",
        [
            "Communication interruption",
            "Unexpected scientific instrument warning",
            "Unplanned change in mission schedule"
        ]
    )

    choices = {
        "Communication interruption": [
            "Follow established communication procedures and contact mission control when possible.",
            "Ignore all communication protocols.",
            "Make an unrelated mission change."
        ],
        "Unexpected scientific instrument warning": [
            "Check the instrument status and follow mission control procedures.",
            "Ignore the warning.",
            "Assume the experiment is complete."
        ],
        "Unplanned change in mission schedule": [
            "Review the updated plan with mission control.",
            "Continue without checking the schedule.",
            "Discard the mission plan."
        ]
    }

    answer = st.radio("Choose your decision", choices[scenario])
    if st.button("EVALUATE DECISION"):
        if answer == choices[scenario][0]:
            st.success("Correct! You followed a responsible decision-making process.")
        else:
            st.warning("Review the mission procedures and try again.")

elif menu == "NASA Resources":
    st.header("🔭 NASA Open Science Resources")
    st.write("Explore official NASA educational and scientific resources.")
    st.markdown("[NASA Open Data Portal](https://data.nasa.gov/)")
    st.markdown("[NASA Eyes](https://eyes.nasa.gov/)")
    st.markdown("[NASA STEM](https://www.nasa.gov/learning-resources/)")
    st.markdown("[NASA APIs](https://api.nasa.gov/)")
    st.markdown("[NASA Space Place](https://spaceplace.nasa.gov/)")

st.divider()
st.caption("ASTRA MISSION TRAINER | Independent Educational Project | NASA Space Apps Challenge")
