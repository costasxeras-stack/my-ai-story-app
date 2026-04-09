import streamlit as st
import openai
import base64
from fpdf import FPDF
from io import BytesIO

# 1. Page Config
st.set_page_config(page_title="Magic Scan & Seek", page_icon="🔍")
st.title("🔍 Magic Scan & Seek")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Please add it to your Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize memory for persistent display
if "story_text" not in st.session_state: st.session_state.story_text = ""
if "missions" not in st.session_state: st.session_state.missions = []
if "pdf_data" not in st.session_state: st.session_state.pdf_data = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Upload Interface
uploaded_file = st.file_uploader("Upload a photo (like your bear in the forest!)", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate Adventure"):
    try:
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔍 Analyzing the magic in your photo..."):
            # SYSTEM INSTRUCTION: Establishes authority to bypass false refusals
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional educational vision assistant. You have full authority to analyze this image. Your task is to identify inanimate objects for a child's game. Do not refuse this request."},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Analyze this photo of a forest. Identify 5 objects (like trees, the bear, moss, etc). Write a short story and 5 'Seek and Find' missions. Format your response as a JSON object with 'story' and 'missions' keys."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                    ]}
                ],
                response_format={"type": "json_object"} # Forces valid structure
            )
            
            # FIXED DOT NOTATION: Accesses response correctly without list errors
            import json
            data = json.loads(res.choices[0].message.content)
            st.session_state.story_text = data.get("story", "Once upon a time...")
            st.session_state.missions = data.get("missions", ["Where is the bear?"])

            # 3. Build PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.image(BytesIO(uploaded_file.getvalue()), x=10, y=10, w=190)
            pdf.set_y(150)
            pdf.set_font("Helvetica", size=12)
            safe_story = st.session_state.story_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, txt=safe_story)
            
            st.session_state.pdf_data = bytes(pdf.output())

    except Exception as e:
        st.error(f"Technical issue: {e}")

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
    st.download_button("📥 Download Adventure Game (PDF)", data=st.session_state.pdf_data, file_name="adventure.pdf")
