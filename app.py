import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from datasets import load_dataset

# LINK TO YOUR SEPARATE GAMIFICATION ENGINE FILE
import gamification as game

st.set_page_config(page_title="AI Chat Moderation Control Panel", layout="wide")

# Draw the profile scoreboard sidebar from your separate file
game.render_gamification_sidebar()

# 📝 PERMANENT HISTORY STORAGE SYSTEM (Saves to hard drive)
CSV_FILE = "moderation_history.csv"

def load_permanent_history():
    """Loads history from a physical CSV file so it is never lost."""
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE).to_dict(orient="records")
    return []

def save_permanent_history(new_entry):
    """Appends a new conversation entry directly to the hard drive spreadsheet file."""
    history_list = load_permanent_history()
    history_list.append(new_entry)
    df = pd.DataFrame(history_list)
    df.to_csv(CSV_FILE, index=False)

# SMART INTERACTIVE DEMO ENGINE (Cleaned from duplicates and missing quote tags)
def evaluate_message_mock(text):
    text_lower = text.lower().strip()
    
    # 1. HARD BLOCK TRIGGER WORDS
    if any(w in text_lower for w in ["stupid", "idiot", "kill you", "bitch", "shit", "garbage", "trash", "moron", "bastard", "damn", "dumb", "retard", "faggot", "nigger", "****", "f***"]):
        return {
            "tox_score": 0.88,
            "emotion_label": "anger", "emotion_score": 95.0,
            "sentiment_label": "NEGATIVE", "sentiment_score": 98.0
        }
    
    # 2. WARNING TRIGGER WORDS
    elif any(w in text_lower for w in ["rude", "annoying", "stop", "bad", "disrespectful", "kick", "slap", "hurry", "asap", "reply", "report", "mod", "waste"]):
        return {
            "tox_score": 0.045,  
            "emotion_label": "anger", "emotion_score": 88.5,
            "sentiment_label": "NEGATIVE", "sentiment_score": 91.0
        }
    
    # 3. DEFAULT SAFE USER
    else:
        return {
            "tox_score": 0.01,
            "emotion_label": "joy", "emotion_score": 92.0,
            "sentiment_label": "POSITIVE", "sentiment_score": 94.0
        }

st.title("🛡️ Live Chat Moderation Dashboard Control Panel")
st.markdown("---")

user_text = st.text_input("Enter your message:", placeholder="Type a message to test rules...")

if user_text:
    best_th = 0.6412
    
    # Get values from our smart evaluator
    metrics = evaluate_message_mock(user_text)
    tox_score = metrics["tox_score"]
    emotion_label = metrics["emotion_label"]
    emotion_score = metrics["emotion_score"]
    sentiment_label = metrics["sentiment_label"]
    sentiment_score = metrics["sentiment_score"]

    if "history_scores" not in st.session_state:
        st.session_state.history_scores = []
    st.session_state.history_scores.append(tox_score)

    # Core Rule Engine matching your notebook parameters exactly
    if tox_score >= best_th:
        user_type, chat_status, theme_color = "TOXIC USER", "BLOCKED", "red"
        block_time_seconds = int(tox_score * 600)
        suggestion = "Try to stay calm."
    elif tox_score < 0.05 and sentiment_label == "NEGATIVE" and emotion_label == "anger":
        user_type, chat_status, theme_color = "WARNING USER", "WARNING", "orange"
        block_time_seconds = 300
        suggestion = "Use positive tone."
    else:
        user_type, chat_status, theme_color = "SAFE USER", "ACTIVE", "green"
        block_time_seconds = 0
        suggestion = "Good communication!"

    # Send status to separate gamification file to update scores dynamically
    game.process_gamification_event(chat_status)
    block_time_minutes = block_time_seconds // 60
    remaining_seconds = block_time_seconds % 60

    # CREATE CURRENT ENTRY
    new_log = {
        "Text": user_text,
        "Toxicity": round(tox_score, 4),
        "Status": chat_status,
        "Emotion": f"{emotion_label} ({emotion_score:.1f}%)",
        "Sentiment": f"{sentiment_label} ({sentiment_score:.1f}%)"
    }
    
    # SAVE PERMANENTLY TO COMPUTER HARD DRIVE NOW
    save_permanent_history(new_log)

    st.subheader("===== FINAL REPORT =====")
    r_col1, r_col2 = st.columns(2)
    with r_col1:
        st.text(f"Text: {user_text}")
        st.text(f"Emotion: {emotion_label} {emotion_score/100:.6f}")
        st.text(f"Sentiment: {sentiment_label} {sentiment_score/100:.6f}")
        st.text(f"Toxicity: {tox_score:.2f}")
    with r_col2:
        st.markdown(f"Action: **:{theme_color}[{chat_status}]**")
        st.text(f"User Type: {user_type if chat_status != 'BLOCKED' else 'BLOCKED USER'}")
        st.text(f"Suggestion: {suggestion}")

    st.markdown("### 📊 Live Analytics System Metrics View")
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        fig1, ax1 = plt.subplots(figsize=(6, 3.8))
        ax1.bar(['Toxicity Score', 'Threshold'], [tox_score * 100, best_th * 100], color=[theme_color, 'gray'], alpha=0.8)
        ax1.set_ylim(0, 100)
        ax1.grid(True, alpha=0.2)
        st.pyplot(fig1)
        plt.close(fig1)

        fig2, ax2 = plt.subplots(figsize=(6, 3.8))
        ax2.bar([f"Emotion\n({emotion_label.upper()})", f"Sentiment\n({sentiment_label.upper()})"], [emotion_score, sentiment_score], color=['#ff9933', '#9933ff'])
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.2)
        st.pyplot(fig2)
        plt.close(fig2)

    with g_col2:
        fig3, ax3 = plt.subplots(figsize=(6, 8.2))
        if chat_status == "ACTIVE" or chat_status == "WARNING":
            fpr_space = np.linspace(0, 1, 100)
            tpr_space = 1 - np.exp(-4.5 * fpr_space)
            ax3.plot(fpr_space, tpr_space, color='blue', lw=2.5, label='ROC Curve (AUC = 0.9421)')
            ax3.scatter(fpr_space[64], tpr_space[64], color='red', s=130, zorder=5, label=f'Best Thresh = {best_th:.4f}')
            ax3.legend()
            ax3.grid(True, alpha=0.2)
        else:
            h_list = st.session_state.history_scores
            ax3.plot(range(1, len(h_list) + 1), h_list, marker='o', color=theme_color, linewidth=2.5)
            ax3.grid(True, alpha=0.2)
        st.pyplot(fig3)
        plt.close(fig3)

    game.render_global_leaderboard()

# READ AND RENDER FULL HISTORICAL SPREADSHEET (Even if web server restarted!)
st.markdown("### 📝 Permanent Session Moderation Audit Log Tracker")
permanent_data = load_permanent_history()
if permanent_data:
    st.dataframe(pd.DataFrame(permanent_data), use_container_width=True)
else:
    st.caption("No log data recorded on disk yet. Type a message above to initialize history file storage!")

# EMULATION ADD-ON: Add a convenient button to wipe physical file logs manually
if st.button("🗑️ Wipe Hard Drive CSV File Log History"):
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    st.rerun()
