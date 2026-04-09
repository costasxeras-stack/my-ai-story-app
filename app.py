import streamlit as st
import openai
import base64
from fpdf import FPDF
from io import BytesIO

# 1. Setup
st.set_page_config(page_title="Scan & Seek Adventure", page_icon="🔍")
st.title("🔍 Scan & Seek Adventure")
st.subheader("Upload any photo and turn it into a learning game!")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
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
uploaded_file = st.file_uploader("Upload a photo (playroom, park, etc.)", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate Adventure"):
    try:
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔍 Analyzing the photo for hidden magic..."):
            # Step A: Analyze and Generate Story + Missions
            # Using detail:high because there are no people to trigger privacy blocks!
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Identify 5 interesting objects in this photo. Write a fun story for a toddler where these objects come to life. Then, create 5 'Seek and Find' questions (e.g., 'Where is the blue ball? Can you point to it?'). Format: Story: [story text] | Missions: [mission 1, mission 2, etc.]"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                ]}]
            )
            
            raw_content = res.choices[0].message.content
            # Split the story and the missions
            parts = raw_content.split('|')
            st.session_state.story_text = parts[0].replace("Story:", "").strip()
            st.session_state.missions = [m.strip() for m in parts[1].replace("Missions:", "").split('\n') if len(m) > 5]

            # Step B: Build PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.image(BytesIO(uploaded_file.getvalue()), x=10, y=10, w=190)
            pdf.ln(150)
            pdf.set_font("Helvetica", size=12)
            
            # Add Story
            pdf.multi_cell(0, 10, txt=st.session_state.story_text.encode('latin-1', 'replace').decode('latin-1'))
            pdf.add_page()
            pdf.set_font("Helvetica", 'B', 16)
            pdf.cell(0, 10, "Seek and Find Missions!", ln=True)
            pdf.set_font("Helvetica", size=12)
            for m in st.session_state.missions:
                pdf.multi_cell(0, 10, txt=m.encode('latin-1', 'replace').decode('latin-1'))
            
            st.session_state.pdf_data = bytes(pdf.output())

    except Exception as e:
        st.error(f"Error: {e}")

# 3. Display
if uploaded_file:
    st.image(uploaded_file, use_container_width=True)

if st.session_state.story_text:
    st.header("📖 The Story")
    st.write(st.session_state.story_text)
    
    st.header("🎯 Seek and Find Missions")
    st.info("Mother: Read these to your baby and have them point to the photo!")
    for m in st.session_state.missions:
        st.write(f"👉 {m}")

if st.session_state.pdf_data:
    st.download_button("📥 Download Adventure Game (PDF)", data=st.session_state.pdf_data, file_name="seek_and_find.pdf")
