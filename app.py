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
uploaded_file = st.file_uploader("Upload any photo to start", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    st.image(uploaded_file, caption="The Adventure World", use_container_width=True)

if uploaded_file and st.button("Generate Adventure"):
    try:
        base64_img = encode_image(uploaded_file)
        with st.status("🪄 Weaving a human story...", expanded=True) as status:
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a children's book author. Return JSON with 'story' (string), 'missions' (list of strings), and 'hints' (list of strings). No nested objects inside the lists."},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Step 1: Identify 5 objects. Step 2: Write a toddler story. Step 3: Create 5 simple missions with hints. Return ONLY JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                    ]}
                ],
                response_format={"type": "json_object"}
            )
            
            raw_content = res.choices[0].message.content
            data = json.loads(raw_content)
            
            # Helper to clean any accidental JSON brackets from strings
            def clean(val):
                if isinstance(val, dict):
                    # If AI sent {'mission': 'text'}, just grab the 'text'
                    return list(val.values())[0]
                return str(val)

            st.session_state.story_text = clean(data.get("story", ""))
            
            # Clean missions and hints specifically
            m_list = [clean(m) for m in data.get("missions", [])]
            h_list = [clean(h) for h in data.get("hints", [])]
            st.session_state.missions = list(zip(m_list, h_list))

            # 3. Build PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.image(BytesIO(uploaded_file.getvalue()), x=10, y=10, w=180)
            pdf.set_xy(10, 150)
            pdf.set_font("Helvetica", size=12)
            safe_story = st.session_state.story_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(190, 10, txt=safe_story)
            
            if st.session_state.missions:
                pdf.add_page()
                pdf.set_font("Helvetica", 'B', 16)
                pdf.cell(190, 10, "Seek and Find Missions!", ln=True)
                pdf.ln(10)
                for i, (m, h) in enumerate(st.session_state.missions):
                    pdf.set_x(10)
                    pdf.set_font("Helvetica", 'B', 12)
                    pdf.multi_cell(180, 8, txt=f"{i+1}. Target: {m}".encode('latin-1', 'replace').decode('latin-1'))
                    pdf.set_x(10)
                    pdf.set_font("Helvetica", 'I', 11)
                    pdf.multi_cell(180, 7, txt=f"   Hint for Mom: {h}".encode('latin-1', 'replace').decode('latin-1'))
                    pdf.ln(5)

            st.session_state.pdf_data = bytes(pdf.output())
            status.update(label="✅ Adventure Ready!", state="complete")

    except Exception as e:
        st.error(f"Technical issue: {e}")

# 4. Display Results
if st.session_state.story_text:
    st.header("📖 The Story")
    st.write(st.session_state.story_text)
    
    st.header("🎯 Seek and Find Missions")
    for i, (m, h) in enumerate(st.session_state.missions):
        with st.expander(f"👉 Mission {i+1}: {m}"):
            st.write(f"💡 {h}")

if st.session_state.pdf_data:
    st.download_button("📥 Download PDF", data=st.session_state.pdf_data, file_name="adventure.pdf", mime="application/pdf")
