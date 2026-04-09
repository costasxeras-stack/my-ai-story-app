import streamlit as st
import openai
import base64
from fpdf import FPDF
import requests
from io import BytesIO

st.set_page_config(page_title="Magic Photo Bedtime Story", page_icon="🪄")
st.title("🪄 Magic Photo Bedtime Story")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize memory
if "pages" not in st.session_state:
    st.session_state.pages = []
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

uploaded_file = st.file_uploader("Upload a photo of your child", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Start the Adventure"):
    try:
        st.session_state.pages = []
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔮 Reading the magic in your photo..."):
            # Step A: Identify the scene and objects
            vision_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Look at this photo. Describe the background and 3 interesting objects. Then, write a 5-page bedtime story where these objects come to life around the child. Use 'BREAK' between pages."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                ]}]
            )
            raw_text = vision_res.choices[0].message.content
            raw_pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

            # Step B: Build the PDF with the original photo
            pdf = FPDF()
            img_bytes = BytesIO(uploaded_file.getvalue()) # Use the original photo data

            for i, txt in enumerate(raw_pages):
                st.session_state.pages.append({"text": txt})

                # Add to PDF
                pdf.add_page()
                # Place the original photo on every page
                pdf.image(img_bytes, x=10, y=10, w=190)
                pdf.set_y(210) # Position text below the photo
                pdf.set_font("Helvetica", size=12)
                safe_text = txt.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            # Finalize PDF
            out = pdf.output()
            st.session_state.pdf_bytes = bytes(out)

    except Exception as e:
        st.error(f"Error: {e}")

# 3. Display Results
for i, p in enumerate(st.session_state.pages):
    st.markdown(f"### Page {i+1}")
    st.image(uploaded_file) # Displays your original photo
    st.write(p["text"]) # Displays the AI narrative about your photo
    st.divider()

# 4. Download
if st.session_state.pdf_bytes:
    st.download_button("📥 Download Final PDF", data=st.session_state.pdf_bytes, file_name="magic_story.pdf", mime="application/pdf")
