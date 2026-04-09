import streamlit as st
import openai
from fpdf import FPDF
from io import BytesIO
import base64

# 1. Page Configuration
st.set_page_config(page_title="Magic Photo Bedtime Story", page_icon="🌙")
st.title("🌙 Magic Photo Bedtime Story")

# 2. Account Check
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Please add it to your Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize memory to keep story and PDF safe on screen
if "story_pages" not in st.session_state:
    st.session_state.story_pages = []
if "pdf_ready" not in st.session_state:
    st.session_state.pdf_ready = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 3. User Input
uploaded_file = st.file_uploader("Upload a photo", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate the Magic"):
    try:
        # Reset memory for a fresh story
        st.session_state.story_pages = []
        st.session_state.pdf_ready = None
        
        with st.status("🔮 Finding the magic..."):
            base64_img = encode_image(uploaded_file)
            
            # THE FIX: This call is formatted specifically to avoid 'list' errors
            vision_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe 3 objects in the background. If privacy filters block you, simply write a 5-page magical story about a child exploring a dream world. Put the word 'BREAK' between pages."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                ]}]
            )
            
            # ACCESSING DATA: This notation (.choices[0].message.content) is the ONLY stable way
            raw_text = vision_res.choices[0].message.content
            st.session_state.story_pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

            # 4. Build the PDF
            pdf = FPDF()
            img_data = BytesIO(uploaded_file.getvalue())

            # First Page with Photo
            pdf.add_page()
            pdf.image(img_data, x=10, y=10, w=190)
            pdf.ln(160) 
            
            for i, page_text in enumerate(st.session_state.story_pages):
                if i > 0: pdf.add_page() 
                pdf.set_font("Helvetica", size=12)
                # Clean text for PDF encoding safety
                safe_text = page_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            # CONVERT TO BYTES: Fixes the StreamlitAPIException
            st.session_state.pdf_ready = bytes(pdf.output())

    except Exception as e:
        st.error(f"Final Fix Applied. Error details: {e}")

# 5. Show Results on UI
if uploaded_file:
    st.image(uploaded_file, use_container_width=True)

if st.session_state.story_pages:
    st.divider()
    for i, text in enumerate(st.session_state.story_pages):
        st.markdown(f"**Chapter {i+1}**")
        st.write(text)
        st.divider()

# 6. Final Download
if st.session_state.pdf_ready:
    st.download_button(
        label="📥 Download PDF Story", 
        data=st.session_state.pdf_ready, 
        file_name="bedtime_story.pdf", 
        mime="application/pdf"
    )
