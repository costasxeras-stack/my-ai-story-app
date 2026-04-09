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
        with st.status("🪄 Weaving your adventure...", expanded=True) as status:
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a children's book author. Return JSON with 'story' (string), 'objects_found' (list of strings), and 'hints' (list of strings)."},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Step 1: Identify 5 actual objects. Step 2: Write a toddler story using them. Step 3: For each object, create a hint describing its location in the photo. Return ONLY JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                    ]}
                ],
                response_format={"type": "json_object"}
            )
            
            # THE CRITICAL FIX: Added [0] to handle the list correctly
            raw_content = res.choices[0].message.content
            data = json.loads(raw_content)
            
            # Helper to keep text human-friendly
            def clean(val):
                return str(val).strip("{}'[]\"")

            st.session_state.story_text = clean(data.get("story", ""))
            
            # Format questions exactly as requested
            objs = data.get("objects_found", [])
            hints = data.get("hints", [])
            
            formatted_missions = []
            for i in range(len(objs)):
                obj_name = clean(objs[i])
                q = f"Can you see the {obj_name} in the photo?"
                h = clean(hints[i]) if i < len(hints) else "Look closely at the colors!"
                formatted_missions.append((q, h))
            
            st.session_state.missions = formatted_missions

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
                for i, (q, h) in enumerate(st.session_state.missions):
                    pdf.set_x(10)
                    pdf.set_font("Helvetica", 'B', 12)
                    pdf.multi_cell(180, 8, txt=f"{i+1}. {q}".encode('latin-1', 'replace').decode('latin-1'))
                    pdf.set_x(10)
                    pdf.set_font("Helvetica", 'I', 11)
                    pdf.multi_cell(180, 7, txt=f"   Hint: {h}".encode('latin-1', 'replace').decode('latin-1'))
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
    for i, (q, h) in enumerate(st.session_state.missions):
        with st.expander(f"👉 Mission {i+1}: {q}"):
            st.write(f"💡 {h}")

if st.session_state.pdf_data:
    st.download_button("📥 Download PDF", data=st.session_state.pdf_data, file_name="adventure.pdf", mime="application/pdf")
