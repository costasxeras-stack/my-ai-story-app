import streamlit as st
import openai
from fpdf import FPDF
from io import BytesIO
import base64

# 1. Page Configuration
st.set_page_config(page_title="Magic Bedtime Story", page_icon="🌙")
st.title("🌙 Magic Photo Bedtime Story")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Use Session State to keep the story on screen
if "story_pages" not in st.session_state:
    st.session_state.story_pages = []
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Upload Section
uploaded_file = st.file_uploader("Upload photo", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate the Magic"):
    try:
        st.session_state.story_pages = []
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔮 Finding the magic..."):
            # We explicitly ask for a story EVEN IF it can't see details to prevent "I can't see it" errors
            vision_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe 3 objects in the background. If you cannot see them, ignore this and write a 5-page story about a hero exploring a magical room. Put 'BREAK' between pages."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                ]}]
            )
            raw_text = vision_res.choices.message.content
            st.session_state.story_pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

            # 3. Build the PDF
            pdf = FPDF()
            img_data = BytesIO(uploaded_file.getvalue())

            # First Page with Photo
            pdf.add_page()
            pdf.image(img_data, x=10, y=10, w=190)
            pdf.ln(160) 
            
            for i, page_text in enumerate(st.session_state.story_pages):
                if i > 0: pdf.add_page() 
                pdf.set_font("Helvetica", size=12)
                # Clean text for PDF safety
                safe_text = page_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            # FIX: Convert output to bytes so Streamlit can download it
            st.session_state.pdf_data = bytes(pdf.output())

    except Exception as e:
        st.error(f"Error: {e}")

# 4. Display Results
if uploaded_file:
    st.image(uploaded_file, use_container_width=True)

if st.session_state.story_pages:
    st.divider()
    for i, text in enumerate(st.session_state.story_pages):
        st.markdown(f"**Chapter {i+1}**")
        st.write(text)
        st.divider()

# 5. Download Button
if st.session_state.pdf_data:
    st.download_button(
        label="📥 Download PDF Story", 
        data=st.session_state.pdf_data, 
        file_name="bedtime_story.pdf", 
        mime="application/pdf"
    )
