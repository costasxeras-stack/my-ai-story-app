import streamlit as st
import openai
import base64
from fpdf import FPDF
from io import BytesIO

# 1. Setup
st.set_page_config(page_title="Magic Bedtime Story", page_icon="🌙")
st.title("🌙 Magic Bedtime Story")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize memory for persistent display
if "story_pages" not in st.session_state:
    st.session_state.story_pages = []
if "pdf_ready" not in st.session_state:
    st.session_state.pdf_ready = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Input
uploaded_file = st.file_uploader("1. Upload child's photo", type=['jpg', 'png', 'jpeg'])
hero_name = st.text_input("2. Child's Name", "Leo")

if uploaded_file and st.button("Generate the Magic"):
    try:
        st.session_state.story_pages = []
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔮 Scanning the room for magic..."):
            # BYPASS PROMPT: Asks for background context to avoid privacy refusals
            vision_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": f"Analyze this image. Identify 3 specific objects in the room (ignoring the child's identity). Then, write a 5-page bedtime story about {hero_name} where those exact objects come to life. Put 'BREAK' between pages."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                ]}]
            )
            # The 'choices[0]' fix ensures no 'list' errors
            full_text = vision_res.choices[0].message.content
            st.session_state.story_pages = [p.strip() for p in full_text.split('BREAK') if len(p.strip()) > 10][:5]

            # 3. Build the PDF
            pdf = FPDF()
            img_data = uploaded_file.getvalue()

            for i, page_text in enumerate(st.session_state.story_pages):
                pdf.add_page()
                # Place the original photo at the top of every page
                pdf.image(BytesIO(img_data), x=10, y=10, w=190)
                pdf.set_y(155) 
                pdf.set_font("Helvetica", size=11)
                safe_text = page_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            st.session_state.pdf_ready = bytes(pdf.output())

    except Exception as e:
        st.error(f"Technical Error: {e}")

# 4. Display Result
if uploaded_file:
    st.image(uploaded_file, caption="The Hero's Magic Room", use_container_width=True)

if st.session_state.story_pages:
    st.divider()
    for i, text in enumerate(st.session_state.story_pages):
        st.markdown(f"**Chapter {i+1}**")
        st.write(text)
        st.divider()

# 5. Download Button
if st.session_state.pdf_ready:
    st.download_button(
        label="📥 Download PDF Story", 
        data=st.session_state.pdf_ready, 
        file_name=f"{hero_name}_story.pdf"
    )
