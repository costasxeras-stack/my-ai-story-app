import streamlit as st
import openai
import base64
from fpdf import FPDF
from io import BytesIO
import json

# 1. Setup
st.set_page_config(page_title="Magic Scan & Seek", page_icon="🔍")
st.title("🔍 Magic Scan & Seek")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "story_text" not in st.session_state: st.session_state.story_text = ""
if "missions" not in st.session_state: st.session_state.missions = []
if "pdf_data" not in st.session_state: st.session_state.pdf_data = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Upload Interface
uploaded_file = st.file_uploader("Upload your forest photo", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate Adventure"):
    try:
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔍 Scanning every pixel for real objects..."):
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a precise vision assistant. You must ONLY identify objects that are physically present in the pixels of the image. Do not invent objects."},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Task: 1. Identify 5 specific objects clearly visible in this photo. 2. Write a short toddler story using only these objects. 3. Create 5 'Seek and Find' missions for these exact objects. Return ONLY a JSON object with keys 'story' and 'missions'."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                    ]}
                ],
                response_format={"type": "json_object"}
            )
            
            data = json.loads(res.choices[0].message.content)
            st.session_state.story_text = data.get("story", "")
            st.session_state.missions = data.get("missions", [])

            # 3. Build PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.image(BytesIO(uploaded_file.getvalue()), x=10, y=10, w=190)
            pdf.ln(150)
            pdf.set_font("Helvetica", size=12)
            safe_story = st.session_state.story_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, txt=safe_story)
            st.session_state.pdf_data = bytes(pdf.output())

    except Exception as e:
        st.error(f"Issue: {e}")

# 4. Display Results
if uploaded_file:
    st.image(uploaded_file, use_container_width=True)

if st.session_state.story_text:
    st.header("📖 The Story")
    st.write(st.session_state.story_text)
    st.header("🎯 Seek and Find Missions")
    for m in st.session_state.missions:
        st.write(f"👉 {m}")

if st.session_state.pdf_data:
    st.download_button("📥 Download PDF", data=st.session_state.pdf_data, file_name="adventure.pdf")
