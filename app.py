import streamlit as st
import openai
import base64
from fpdf import FPDF
import requests
from io import BytesIO

st.set_page_config(page_title="Bedtime Story AI", page_icon="🌙")
st.title("🌙 Bedtime Story Creator")

# 1. API Setup
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize App Memory
if "pages" not in st.session_state:
    st.session_state.pages = []
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Upload UI
uploaded_file = st.file_uploader("Upload photo of hero", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    try:
        st.session_state.pages = [] 
        
        with st.status("🪄 Creating magic..."):
            # Step A: Hero Analysis
            base64_img = encode_image(uploaded_file)
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [{"type": "text", "text": "Describe the shirt color and pick a woodland animal. Return: 'A [animal] in a [color] shirt'."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}]}]
            )
            hero = char_res.choices[0].message.content

            # Step B: Story Writing
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page story about {hero}. Use 'BREAK' between pages."}]
            )
            raw_text = story_res.choices[0].message.content
            raw_pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

            # Step C: Build Story and PDF
            pdf = FPDF()
            for i, txt in enumerate(raw_pages):
                # Image Gen
                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Watercolor illustration: {hero} in {txt[:100]}. No humans.",
                    n=1, size="1024x1024"
                )
                url = img_gen.data[0].url
                
                # FIX for '_io.BytesIO' object has no attribute 'rfind'
                # We download the image and give it a fake name so FPDF knows it's a JPEG
                img_data = requests.get(url).content
                img_stream = BytesIO(img_data)
                
                # Save to app memory
                st.session_state.pages.append({"text": txt, "url": url})

                # Add to PDF
                pdf.add_page()
                # We use the 'name' parameter to tell FPDF this is a JPG
                pdf.image(img_stream, x=10, y=10, w=190, type='JPG')
                pdf.ln(200)
                pdf.set_font("Helvetica", size=12)
                pdf.multi_cell(0, 10, txt=txt.encode('latin-1', 'replace').decode('latin-1'))

            # Finalize PDF
            out = pdf.output(dest='S')
            st.session_state.pdf_bytes = out.encode('latin-1') if isinstance(out, str) else out

    except Exception as e:
        st.error(f"Error: {e}")

# 3. Display Results (This stays visible because of session_state)
for i, p in enumerate(st.session_state.pages):
    st.markdown(f"### Page {i+1}")
    st.image(p["url"])
    st.write(p["text"])
    st.divider()

# 4. Download
if st.session_state.pdf_bytes:
    st.download_button("📥 Download PDF Story", data=st.session_state.pdf_bytes, file_name="story.pdf", mime="application/pdf")
