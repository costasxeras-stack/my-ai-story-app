import streamlit as st
import openai
from fpdf import FPDF
from io import BytesIO

# 1. Setup
st.set_page_config(page_title="Magic Adventure & Learn", page_icon="🚀")
st.title("🚀 Magic Adventure & Learn")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Memory
if "story_pages" not in st.session_state:
    st.session_state.story_pages = []
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []
if "pdf_ready" not in st.session_state:
    st.session_state.pdf_ready = None

# 2. Inputs
uploaded_file = st.file_uploader("1. Upload hero's photo", type=['jpg', 'png', 'jpeg'])
hero_name = st.text_input("2. Hero's Name", "Leo")
magic_items = st.text_input("3. What's in the room?", "a blue truck and a soft rug")

if uploaded_file and st.button("Start Adventure"):
    try:
        st.session_state.story_pages = []
        st.session_state.flashcards = []
        
        with st.status("🪄 Preparing adventure and learning games..."):
            # A. Generate Story + Flashcards in one go
            prompt = f"Write a 3-page adventure for {hero_name} with {magic_items}. Then, create 3 'Magic Learning' missions. Format: Page 1 | Page 2 | Page 3 | Mission 1 | Mission 2 | Mission 3"
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            raw_parts = res.choices.message.content.split('|')
            
            # Separate Story and Missions
            story_data = [p.strip() for p in raw_parts[:3]]
            mission_data = [p.strip() for p in raw_parts[3:6]]

            # B. Build PDF and Audio
            pdf = FPDF()
            img_data = uploaded_file.getvalue()

            for i, text in enumerate(story_data):
                # Voice Narration
                audio_res = client.audio.speech.create(model="tts-1", voice="nova", input=text)
                st.session_state.story_pages.append({"text": text, "audio": audio_res.content})

                # PDF Page
                pdf.add_page()
                pdf.image(BytesIO(img_data), x=10, y=10, w=190)
                pdf.ln(160)
                pdf.set_font("Helvetica", size=12)
                pdf.multi_cell(0, 10, txt=text.encode('latin-1', 'replace').decode('latin-1'))

            st.session_state.flashcards = mission_data
            st.session_state.pdf_ready = bytes(pdf.output())

    except Exception as e:
        st.error(f"Error: {e}")

# 3. Display
if uploaded_file:
    st.image(uploaded_file, use_container_width=True)

# THE STORY
for i, page in enumerate(st.session_state.story_pages):
    st.markdown(f"### Chapter {i+1}")
    st.audio(page["audio"], format="audio/mp3")
    st.write(page["text"])
    st.divider()

# THE FLASHCARDS (Learning Feature)
if st.session_state.flashcards:
    st.header("🌟 Magic Learning Missions")
    cols = st.columns(3)
    for i, mission in enumerate(st.session_state.flashcards):
        with cols[i]:
            st.info(f"**Mission {i+1}**\n\n{mission}")

# 4. Download
if st.session_state.pdf_ready:
    st.download_button("📥 Download Adventure PDF", data=st.session_state.pdf_ready, file_name="adventure.pdf")
