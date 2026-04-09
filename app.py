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

# Initialize memory
if "story_text" not in st.session_state: st.session_state.story_text = ""
if "missions" not in st.session_state: st.session_state.missions = []
if "pdf_data" not in st.session_state: st.session_state.pdf_data = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Universal Upload Interface
uploaded_file = st.file_uploader("Upload any photo to start the adventure", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate Adventure"):
    try:
        st.session_state.story_text = "" 
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔍 Scanning for hidden magic..."):
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a precise vision assistant. Identify 5 objects. Return ONLY JSON with 'story', 'missions' (the question), and 'hints' (where the object is)."},
                    {"role": "user", "content": [
                        {"type": "text", "text": "1. Identify 5 objects. 2. Write a toddler story. 3. Create 5 'Seek and Find' missions with hints. Return ONLY JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                    ]}
                ],
                response_format={"type": "json_object"}
            )
            
            data = json.loads(res.choices.message.content)
            st.session_state.story_text = data.get("story", "")
            
            missions = data.get("missions", [])
            hints = data.get("hints", [])
            st.session_state.missions = list(zip(missions, hints))

            # 3. Build PDF (Fixing horizontal space error)
            pdf = FPDF()
            
            # Page 1: Photo and Story
            pdf.add_page()
            pdf.image(BytesIO(uploaded_file.getvalue()), x=10, y=10, w=180)
            # Ensure we move the "Y" cursor well below the image
            pdf.set_y(140) 
            pdf.set_font("Helvetica", size=12)
            
            safe_story = st.session_state.story_text.encode('latin-1', 'replace').decode('latin-1')
            # Using width=0 tells the PDF to use all available horizontal space automatically
            pdf.multi_cell(0, 10, txt=safe_story)
            
            # Page 2: Missions
            pdf.add_page()
            pdf.set_font("Helvetica", 'B', 16)
            pdf.cell(0, 10, "Target: Seek and Find Missions!", ln=True)
            pdf.ln(5)
            
            for i, (m, h) in enumerate(st.session_state.missions):
                pdf.set_font("Helvetica", 'B', 12)
                m_text = f"Mission {i+1}: {m}"
                pdf.multi_cell(0, 10, txt=m_text.encode('latin-1', 'replace').decode('latin-1'))
                
                pdf.set_font("Helvetica", size=12)
                h_text = f"Hint: {h}"
                pdf.multi_cell(0, 10, txt=h_text.encode('latin-1', 'replace').decode('latin-1'))
                pdf.ln(5)

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
    for i, (m, h) in enumerate(st.session_state.missions):
        with st.expander(f"👉 Mission {i+1}: {m}"):
            st.write(f"💡 **Hint for Mom:** {h}")

if st.session_state.pdf_data:
    st.download_button("📥 Download Complete Adventure PDF", data=st.session_state.pdf_data, file_name="adventure_game.pdf")
