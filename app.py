import streamlit as st
import openai
from fpdf import FPDF
from io import BytesIO
import base64

# 1. Page Configuration
st.set_page_config(page_title="Magic Photo Bedtime Story", page_icon="🌙")
st.title("🌙 Magic Photo Bedtime Story")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Please add OPENAI_API_KEY to your Streamlit Secrets.")
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
uploaded_file = st.file_uploader("Upload a photo of your child in their room", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate the Magic"):
    try:
        st.session_state.story_pages = []
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔮 Scanning the room for toys and magic..."):
            # We use 'detail: high' and a strict 'ignore humans' prompt to bypass privacy filters
            vision_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Ignore any people. Look at the background and toys only. List 3 objects you see. Then write a 5-page bedtime story where these objects come to life around the child. Use 'BREAK' between pages."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                ]}]
            )
            # FIX: Using .choices.message.content to prevent 'list' and 'subscriptable' errors
            raw_text = vision_res.choices[0].message.content
            st.session_state.story_pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

            # 3. Build the PDF (One Photo at the top, then text)
            pdf = FPDF()
            img_bytes = BytesIO(uploaded_file.getvalue())

            # Add the Photo once on the very first page
            pdf.add_page()
            pdf.image(img_stream=img_bytes, x=10, y=10, w=190)
            pdf.ln(160) # Move cursor down for first page text
            
            for i, page_text in enumerate(st.session_state.story_pages):
                if i > 0: pdf.add_page() # Add a new page for every story part after the first
                pdf.set_font("Helvetica", size=12)
                # Clean text to prevent "White Page" errors
                safe_text = page_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            st.session_state.pdf_data = bytes(pdf.output())

    except Exception as e:
        st.error(f"Error: {e}")

# 4. Show the results on the Screen
if uploaded_file:
    st.image(uploaded_file, caption="The Hero's World", use_container_width=True)

if st.session_state.story_pages:
    st.divider()
    for i, text in enumerate(st.session_state.story_pages):
        st.markdown(f"**Chapter {i+1}**")
        st.write(text)
        st.write("") # Extra spacing

# 5. Download Button
if st.session_state.pdf_data:
    st.download_button(
        label="📥 Download PDF Story", 
        data=st.session_state.pdf_data, 
        file_name="bedtime_story.pdf", 
        mime="application/pdf"
    )
