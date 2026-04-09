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

# 2. Upload
uploaded_file = st.file_uploader("Upload any photo to start", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate Adventure"):
    try:
        base64_img = encode_image(uploaded_file)
        with st.status("🪄 Analyzing real objects in your photo...", expanded=True) as status:
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a literal vision assistant. ONLY use objects clearly visible in the pixels. Return JSON with 'story', 'missions', and 'hints'."},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Step 1: Look at the photo and identify 5 actual objects and their colors. Step 2: Write a toddler story using ONLY these objects. Step 3: Create 5 missions with hints. Return ONLY JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                    ]}
                ],
                response_format={"type": "json_object"}
            )
            
            raw_content = res.choices[0].message.content
            data = json.loads(raw_content)
            st.session_state.story_text = data.get("story", "")
            st.session_state.missions = list(zip(data.get("missions", []), data.get("hints", [])))

            # 3. Build PDF (The Layout Fix)
            pdf = FPDF()
            
            # Page 1: Photo + Story
            pdf.add_page()
            pdf.image(BytesIO(uploaded_file.getvalue()), x=10, y=10, w=180)
            pdf.set_xy(10, 150) # Reset pen to the left margin
            pdf.set_font("Helvetica", size=12)
            safe_story = st.session_state.story_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(190, 10, txt=safe_story)
            
            # Page 2: Missions (The Alignment Fix)
            if st.session_state.missions:
                pdf.add_page()
                pdf.set_font("Helvetica", 'B', 16)
                pdf.cell(190, 10, "Seek and Find Missions!", ln=True)
                pdf.ln(10)
                
                for m, h in st.session_state.missions:
                    # Reset X to 10 for every line to prevent the "right-sliding" text
                    pdf.set_x(10)
                    pdf.set_font("Helvetica", 'B', 12)
                    pdf.multi_cell(180, 8, txt=f"Target: {m}".encode('latin-1', 'replace').decode('latin-1'))
                    
                    pdf.set_x(10) # Reset X again for the hint
                    pdf.set_font("Helvetica", 'I', 11)
                    pdf.multi_cell(180, 7, txt=f"Hint for Mom: {h}".encode('latin-1', 'replace').decode('latin-1'))
                    pdf.ln(5)

            st.session_state.pdf_data = bytes(pdf.output())
            status.update(label="✅ Adventure Ready!", state="complete")

    except Exception as e:
        st.error(f"Technical issue: {e}")

# 4. Display
if uploaded_file:
    st.image(uploaded_file, use_container_width=True)

if st.session_state.story_text:
    st.header("📖 The Story")
    st.write(st.session_state.story_text)
    st.header("🎯 Seek and Find Missions")
    for i, (m, h) in enumerate(st.session_state.missions):
        with st.expander(f"👉 Mission {i+1}: {m}"):
            st.write(f"💡 {h}")

if st.session_state.pdf_data:
    st.download_button("📥 Download PDF", data=st.session_state.pdf_data, file_name="adventure.pdf", mime="application/pdf")
