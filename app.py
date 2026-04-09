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

# Initialize memory so data survives button clicks
if "story_text" not in st.session_state: st.session_state.story_text = ""
if "missions" not in st.session_state: st.session_state.missions = []
if "pdf_data" not in st.session_state: st.session_state.pdf_data = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Upload Interface
uploaded_file = st.file_uploader("Upload any photo to start", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate Adventure"):
    try:
        base64_img = encode_image(uploaded_file)
        
        with st.status("🪄 Working on it...", expanded=True) as status:
            st.write("🔍 Analyzing photo...")
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a precise vision assistant. Return ONLY valid JSON with keys 'story', 'missions' (list), and 'hints' (list)."},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Identify 5 objects. Write a toddler story and 5 missions with hints. Return ONLY JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                    ]}
                ],
                response_format={"type": "json_object"}
            )
            
            # --- THE "ALL-IN-ONE" FIXES START HERE ---
            # Fix 1: Use .choices[0].message.content (Correct Access)
            raw_content = res.choices[0].message.content
            
            # Fix 2: Check if content is empty (Prevents NoneType Error)
            if not raw_content:
                st.error("AI returned an empty response. Please try again.")
                st.stop()
                
            data = json.loads(raw_content)
            st.session_state.story_text = data.get("story", "")
            missions = data.get("missions", [])
            hints = data.get("hints", [])
            st.session_state.missions = list(zip(missions, hints))

            st.write("📄 Creating PDF...")
            pdf = FPDF()
            
            # PAGE 1: Photo + Story
            pdf.add_page()
            # Fix 3: Image width slightly smaller for safety
            pdf.image(BytesIO(uploaded_file.getvalue()), x=10, y=10, w=180)
            
            # Fix 4: Set XY to 150 to ensure enough horizontal/vertical space
            pdf.set_xy(10, 150) 
            pdf.set_font("Helvetica", size=12)
            
            # Fix 5: latin-1 replace handles curly quotes and emojis that crash FPDF
            safe_story = st.session_state.story_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(190, 10, txt=safe_story)
            
            # PAGE 2: Missions
            if st.session_state.missions:
                pdf.add_page()
                pdf.set_xy(10, 20)
                pdf.set_font("Helvetica", 'B', 16)
                pdf.cell(0, 10, "Seek and Find Missions!", ln=True)
                pdf.ln(5)
                for m, h in st.session_state.missions:
                    pdf.set_font("Helvetica", 'B', 12)
                    pdf.multi_cell(190, 8, txt=f"Mission: {m}".encode('latin-1', 'replace').decode('latin-1'))
                    pdf.set_font("Helvetica", size=11)
                    pdf.multi_cell(190, 7, txt=f"Hint: {h}".encode('latin-1', 'replace').decode('latin-1'))
                    pdf.ln(4)

            # Fix 6: Convert to raw bytes to prevent Streamlit download crash
            st.session_state.pdf_data = bytes(pdf.output())
            status.update(label="✅ Magic Complete!", state="complete", expanded=False)

    except Exception as e:
        st.error(f"Technical issue: {e}")

# 3. Display Results
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
    st.download_button("📥 Download PDF Story", data=st.session_state.pdf_data, file_name="adventure.pdf", mime="application/pdf")
