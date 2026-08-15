import streamlit as st
from dotenv import load_dotenv

import google.generativeai as genai
import json
import os

# .env config
load_dotenv()

# API Setup

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")
# Configure Gemini
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.0-flash")

#load JSON Reviews

with open("university_reviews.json", "r", encoding="utf-8") as f:
    reviews_data = json.load(f)

# Streamlit

st.set_page_config(page_title = "University comparison Bot", page_icon = "🎓")
st.title("🎓 University comparison bot (Pakistant)")
st.write("Compare Universities based on Reddit student Reviews!")

#Comparison of Colleges:
colleges = list(reviews_data.keys())
selected_uni1 = st.selectbox("Choose a University :",colleges)
compare_mode = st.checkbox("Compare with another University")
selected_uni2 = None
if compare_mode:
    selected_uni2 = st.selectbox("Choose a second university:", [c for c in colleges if c != selected_uni1])

if st.button("Get Insights"):
    if not compare_mode:
        # Summarize reviews of one university
        reviews_text = " ".join(reviews_data[selected_uni1]["positive"] + reviews_data[selected_uni1]["negative"])
        prompt = f"""
        Based on the following student reviews of {selected_uni1}, provide 3 pros and 3 cons in bullet points:
        {reviews_text}
        """
    else:
        reviews1 = " ".join(reviews_data[selected_uni1]["positive"] + reviews_data[selected_uni1]["negative"])
        reviews2 = " ".join(reviews_data[selected_uni2]["positive"] + reviews_data[selected_uni2]["negative"])
        prompt = f"""
        Compare these two universities based on student reviews.

        University 1: {selected_uni1}
        Reviews: {reviews1}

        University 2: {selected_uni2}
        Reviews: {reviews2}

        Provide a short summary of strengths and weaknesses of each, and who each university is better suited for.
        """

    # Final Step: Call the model inside the button block
    with st.spinner("Thinking..."):
        response = model.generate_content(prompt)
        st.subheader("🎯 Recommendation:")
        st.write(response.text)