import streamlit as st
from PIL import Image
import pandas as pd
import plotly.express as px
from logic import analyze_wound, get_detailed_report
import datetime

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="AI Wound Healing Monitor")

# --- Initialize Session State ---
# This is like a browser's memory, it will remember the data
if 'history' not in st.session_state:
    st.session_state.history = []

# --- UI ---
st.title("🩺 AI Wound Healing Monitor 2.0")
st.write("Upload a wound image for an advanced analysis, including healing velocity tracking.")

st.sidebar.header("Upload Image")
uploaded_file = st.sidebar.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    original_image = Image.open(uploaded_file)
    
    # Perform analysis
    processed_image, wound_area, color_analysis = analyze_wound(original_image)
    report = get_detailed_report(wound_area, color_analysis)
    
    # --- New Feature: Auto-generate wound description ---
    wound_description = ""
    if wound_area < 2000:
        wound_description = "Small wound, minimal tissue damage."
    elif wound_area < 10000:
        wound_description = "Moderate wound, some inflammation observed."
    else:
        wound_description = "Large wound, significant tissue involvement. Monitor closely."
    
    # Combine with AI report description
    full_description = f"{report['description']} {wound_description}"
    
    # Store the new record in history
    new_record = {
        "date": datetime.datetime.now(),
        "healing_score": report["healing_score"],
        "wound_area": report["wound_area"]
    }
    st.session_state.history.append(new_record)
    
    # --- Display Layout ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Image Analysis")
        st.image(processed_image, caption="Processed Image with Area Calculation", use_column_width=True)
        
    with col2:
        st.subheader("AI Analysis Report")
        
        st.markdown(f"**Description:** *{full_description}*")
        
        c1, c2, c3 = st.columns(3)
        
        # --- New Feature: Battery-style healing score ---
        def battery_style(score):
            """Return a colored bar representing healing score as battery."""
            if score > 75:
                color = "green"
            elif score > 50:
                color = "yellow"
            elif score > 25:
                color = "orange"
            else:
                color = "red"
            bar = f"<div style='width:100px; border:1px solid #000;'><div style='width:{score}%; background-color:{color}; height:20px'></div></div> {score}%"
            return bar

        c1.markdown("**Healing Score**", unsafe_allow_html=True)
        c1.markdown(battery_style(report['healing_score']), unsafe_allow_html=True)
        
        c2.metric("Infection Risk", report['infection_risk'])
        c3.metric("Wound Area (px²)", f"{report['wound_area']:,}") # Formats number with commas

    st.markdown("---")
    
    # --- Healing Velocity Graph ---
    st.subheader("🚀 Healing Velocity")
    
    if len(st.session_state.history) > 1:
        # Create a DataFrame from the history
        df = pd.DataFrame(st.session_state.history)
        
        # Create the graph
        fig = px.line(df, x='date', y='healing_score', title='Healing Score Over Time',
                      markers=True, labels={"date": "Date of Analysis", "healing_score": "Healing Score (%)"})
        fig.update_layout(title_font_size=20, xaxis_title_font_size=16, yaxis_title_font_size=16)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Upload another image on a different day to see the healing progress graph.")
        
else:
    st.info("Please upload an image to begin the analysis.")
