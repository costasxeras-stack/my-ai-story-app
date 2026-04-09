import streamlit as st
import openai
import base64
from fpdf import FPDF
from io import BytesIO

# 1. Setup
st.set_page_config(page_title="Scan & Seek Adventure", page_icon="🔍")
st.title("🔍 Scan & Seek Adventure")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Please add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize memory
if "story_text" not in st.session_state:
    st.session_state.story_text = ""
if "missions" not in st.session_state:
    st.session_state.missions = []
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Upload
uploaded_file = st.file_uploader("Upload a photo (playroom, garden, etc.)", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate Adventure"):
    try:
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔍 Scanning for hidden magic..."):
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Identify 5 objects in this photo. Write a short toddler story about them. Then, add 5 'Seek and Find' questions. Format: Story: [text] | Missions: [list]."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                ]}]
            )
            
            # THE FIX: Safely read the response
            full_msg = res.choices[0].message.content
            
            if "|" in full_msg:
                parts = full_msg.split('|')
                st.session_state.story_text = parts[0].replace("Story:", "").strip()
                st.session_state.missions = [m.strip() for m in parts[1].replace("Missions:", "").split('\n') if len(m) > 5]
            else:
                # Fallback if AI forgets the "|" symbol
                st.session_state.story_text = full_msg
                st.session_state.missions = ["Can you find something red?", "Where is the biggest toy?"]

            # Build PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.image(BytesIO(uploaded_file.getvalue()), x=10, y=10, w=190)
            pdf.ln(150)
            pdf.set_font("Helvetica", size=12)
            
            # Clean text for PDF
            clean_story = st.session_state.story_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, txt=clean_story)
            
            # Finalize PDF bytes
            st.session_state.pdf_data = bytes(pdf.output())

    except Exception as e:
        st.error(f"Technical issue: {e}")

# 3. Display
if uploaded_file:
    st.image(uploaded_file, use_container_width=True)

if st.session_state.story_text:
    st.header("📖 The Story")
    st.write(st.session_state.story_text)
    
    st.header("🎯 Seek and Find Missions")
    for m in st.session_state.missions:
        st.write(f"👉 {m}")

# 4. Download
if st.session_state.pdf_data:
    st.download_button("📥 Download Adventure Game (PDF)", data=st.session_state.pdf_data, file_name="adventure.pdf")
