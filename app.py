import streamlit as st
import openai
from fpdf import FPDF
from io import BytesIO
import base64

# 1. Page Configuration
st.set_page_config(page_title="Magic Bedtime Story", page_icon="🌙")
st.title("🌙 Magic Photo Bedtime Story")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Please add OPENAI_API_KEY to your Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "story_pages" not in st.session_state:
    st.session_state.story_pages = []
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Upload Section
uploaded_file = st.file_uploader("Upload a photo of the hero's room", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate the Magic"):
    try:
        st.session_state.story_pages = []
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔮 Finding the magic in your photo..."):
            # Prompt designed to bypass privacy filters by focusing on background
            vision_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Ignore people. Describe 3 specific objects in the background. Write a 5-page bedtime story where these items come to life. Put 'BREAK' between pages."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                ]}]
            )
            raw_text = vision_res.choices[0].message.content
            st.session_state.story_pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

            # 3. Build the PDF
            pdf = FPDF()
            # FIX: Convert the uploaded file to BytesIO
            img_data = BytesIO(uploaded_file.getvalue())

            # Add Photo once on the first page
            pdf.add_page()
            # FIX: Use 'name' or no keyword instead of 'img_stream'
            pdf.image(img_data, x=10, y=10, w=190)
            pdf.ln(160) 
            
            for i, page_text in enumerate(st.session_state.story_pages):
                if i > 0: pdf.add_page() 
                pdf.set_font("Helvetica", size=12)
                safe_text = page_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            st.session_state.pdf_data = pdf.output()

    except Exception as e:
        st.error(f"Error: {e}")

# 4. Show Results
if uploaded_file:
    st.image(uploaded_file, caption="The Magic Room", use_container_width=True)

if st.session_state.story_pages:
    st.divider()
    for i, text in enumerate(st.session_state.story_pages):
        st.markdown(f"**Page {i+1}**")
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
