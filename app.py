import streamlit as st
import boto3
import json
import time
import requests
import random

# Constants
S3_BUCKET = "pt-dataset-bucket-567"
S3_KEY = "pt-questions.json"
API_URL = "https://icwkdnl7sb.execute-api.us-east-1.amazonaws.com/ask"
TOTAL_TIME = 1800  # 30 minutes
NUM_QUESTIONS = 10
MARKS_PER_QUESTION = 2
MAX_MARKS = NUM_QUESTIONS * MARKS_PER_QUESTION
PASS_MARKS = int(MAX_MARKS * 0.7)

# Page Config
st.set_page_config(page_title="Practice Test Assistant 🎉", layout="wide")

# Custom Styling
st.markdown("""
<style>
/* Gradient Background (Whizlabs Theme: Orange → Red → White) */
.stApp { 
    background: linear-gradient(135deg, #ff6600 0%, #ff2e2e 50%, #ffffff 100%); 
    font-family: 'Arial', sans-serif; 
    color: white;
}

/* Title with dark color */
.title { 
    font-size: 2.5rem; 
    font-weight: bold; 
    text-align: center; 
    color: black;  /* Changed from gradient to black for visibility */
    margin-top: 10px;
}

/* Subtitle */
.subtitle { 
    font-size: 1.2rem; 
    text-align: center; 
    color: #f8f8f8; 
    margin-bottom: 10px;
}

/* Centered Logo */
.logo-container {
    text-align: center;
    margin-top: 10px;
    margin-bottom: -10px;
}
.logo-container img {
    width: 100px;
    height: auto;
}

/* Question Box */
.question-box { 
    background: linear-gradient(135deg, #ffe29f 0%, #ffa99f 100%); 
    padding: 20px; 
    border-radius: 12px; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.2); 
    color: #000; 
}

/* AI Box */
.ai-box { 
    background: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%); 
    padding: 15px; 
    border-radius: 12px; 
    margin-top: 15px; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    color: #000;
}

/* Timer */
.timer { 
    font-size: 1.2rem; 
    font-weight: bold; 
    color: #ffecec; 
}

/* Buttons */
button { 
    border-radius: 8px; 
    background: linear-gradient(135deg, #ff6600 0%, #ff2e2e 100%); 
    color: white; 
    padding: 10px 20px; 
    border: none; 
    font-weight: bold; 
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}

/* Success / Error */
.success { color: #00ff9d; font-weight: bold; }
.error { color: #ffb3b3; font-weight: bold; }

/* Result Box */
.result-box { 
    background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); 
    padding: 20px; 
    border-radius: 15px; 
    color: #000; 
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# Logo at the top center
st.markdown(
    f"""
    <div class="logo-container">
        <img src="https://play-lh.googleusercontent.com/pUxNfrcwglo40Se238mGSMCQwBI-8niKDse6zdvgVnR4iCkQMckNqoE_WhcCSQVz9w" alt="Whizlabs Logo">
    </div>
    """,
    unsafe_allow_html=True,
)

# Title
st.markdown('<div class="title">Practice Test Assistant 🎉</div>', unsafe_allow_html=True)

# Fetch questions and pick random 10
@st.cache_data
def load_questions():
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
    all_questions = json.loads(obj["Body"].read().decode("utf-8"))
    return random.sample(all_questions, NUM_QUESTIONS)

questions = load_questions()

# Session State
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "checked_answers" not in st.session_state:
    st.session_state.checked_answers = {}
if "time_remaining" not in st.session_state:
    st.session_state.time_remaining = TOTAL_TIME
if "paused" not in st.session_state:
    st.session_state.paused = False
if "practice_mode" not in st.session_state:
    st.session_state.practice_mode = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "submitted_once" not in st.session_state:
    st.session_state.submitted_once = False # prevent multiple scoring

# Timer function
def update_timer():
    if st.session_state.quiz_started and not st.session_state.paused:
        elapsed = time.time() - st.session_state.start_time
        st.session_state.time_remaining = max(0, TOTAL_TIME - int(elapsed))
        if st.session_state.time_remaining == 0:
            submit_quiz()

# Pause/Resume
def pause_quiz():
    st.session_state.paused = True

def resume_quiz():
    st.session_state.paused = False
    st.session_state.start_time = time.time() - (TOTAL_TIME - st.session_state.time_remaining)

# Submit and evaluate (only first submit counts)
def submit_quiz():
    if not st.session_state.submitted_once: # lock first attempt
        st.session_state.quiz_started = False
        correct = sum(1 for i in range(len(questions)) 
                      if st.session_state.checked_answers.get(i) == questions[i]["correct_answer"])
        st.session_state.correct = correct
        st.session_state.total = len(questions)
        st.session_state.score = correct * MARKS_PER_QUESTION
        st.session_state.submitted_once = True

# Check answer
def check_answer():
    q_idx = st.session_state.current_question
    selected = st.session_state.answers.get(q_idx)
    correct = questions[q_idx]["correct_answer"]
    st.session_state.checked_answers[q_idx] = selected
    if selected == correct:
        st.session_state.feedback = "Correct! ✅ Nice move!"
    else:
        st.session_state.feedback = "Wrong! ❌ Almost there!"

# Main App
if not st.session_state.quiz_started:
    st.markdown('<div class="subtitle">Exam Instructions 🚀</div>', unsafe_allow_html=True)
    st.write("""
    The exam comprises:
    - Multiple Choice Single Response (MCSR)
    - Multiple Choice Multiple Response (MCMR)
    No negative marking.
    A timer ⏰ in the top-right corner shows time left.
    """)

    st.markdown('<div class="subtitle">Exam Details 🎯</div>', unsafe_allow_html=True)
    st.write(f"Questions: {NUM_QUESTIONS}")
    st.write("Time: 30 minutes")
    st.write(f"Max. Marks: {MAX_MARKS}")
    st.write(f"Passing: 70% ({PASS_MARKS} marks)")

    if not st.session_state.submitted_once: # allow start only before submit
        if st.button("Start Quiz 🚀"):
            st.session_state.practice_mode = True
            st.session_state.quiz_started = True
            st.session_state.start_time = time.time()

# Results Section
if "score" in st.session_state:
    st.markdown('<div class="subtitle">Final Results 🎊</div>', unsafe_allow_html=True)
    correct = st.session_state.correct
    total = st.session_state.total
    score = st.session_state.score
    wrong = total - correct
    percent = (score / MAX_MARKS) * 100

    # Result Box
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.write(f"✅ Correct: {correct} | ❌ Wrong: {wrong}")
    st.write(f"🏆 Score: **{score} / {MAX_MARKS}**")
    st.write(f"📊 Percentage: **{percent:.2f}%**")

    if score >= PASS_MARKS:
        st.success("🎉 Hurray! You're Genius 🤩🔥")
        st.balloons()
        st.snow()
    else:
        st.error("😅 Leave it buddy! You can do it! Come fully prepared tomorrow 💪")
        st.balloons()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    update_timer()
    q_idx = st.session_state.current_question
    q = questions[q_idx]

    st.markdown(f'<div class="question-box"><b>Question {q_idx + 1}:</b> {q["question_text"]}</div>', unsafe_allow_html=True)

    # Timer
    st.sidebar.markdown(f'<div class="timer">Time Remaining ⏰: {st.session_state.time_remaining // 60}:{st.session_state.time_remaining % 60:02d}</div>', unsafe_allow_html=True)
    if st.sidebar.button("Pause Quiz ⬅️"):
        pause_quiz()
    if st.session_state.paused:
        if st.sidebar.button("Continue 🚀"):
            resume_quiz()

    # Options
    selected = st.radio("Select Answer:", list(q["options"].values()), key=f"q{q_idx}")
    opt_key = [k for k, v in q["options"].items() if v == selected][0]
    st.session_state.answers[q_idx] = opt_key

    # Check Answer
    if st.button("Check Answer ✅"):
        check_answer()
    if q_idx in st.session_state.checked_answers:
        st.markdown(f'<div class="{ "success" if st.session_state.feedback.startswith("Correct") else "error" }">{st.session_state.feedback}</div>', unsafe_allow_html=True)

    # AI Box
    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
    st.subheader("Ask AI about this question 🤖")
    user_query = st.text_input("E.g., 'Why is option A incorrect?'", key=f"query{q_idx}")
    if st.button("Ask AI 🚀", key=f"ask{q_idx}"):
        payload = {"qid": q["qid"], "question": user_query, "user_id": "student1"}
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(API_URL, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("answer") == "Sorry, I am unable to assist you with this request.":
                    st.error("AI Response: No specific answer found ❌")
                else:
                    st.write(f"AI Answer: {data['answer']} (Source: {data['source']}) 🎯")
            else:
                st.error(f"Error querying AI: {response.text} ❌")
        except Exception as e:
            st.error(f"Error: {str(e)} ❌")
    st.markdown('</div>', unsafe_allow_html=True)

    # Navigation
    col1, col2 = st.columns(2)
    if col1.button("Previous ⬅️", disabled=(q_idx == 0)):
        st.session_state.current_question -= 1
    if col2.button("Next ➡️", disabled=(q_idx == len(questions) - 1)):
        st.session_state.current_question += 1
    if st.button("Submit Quiz 🎯"):
        submit_quiz()

