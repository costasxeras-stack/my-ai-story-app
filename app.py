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
    st.error("Missing API Key in Secrets!")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize App Memory
if "pages" not in st.session_state:
    st.session_state.pages = []
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Upload UI
uploaded_file = st.file_uploader("Upload photo of hero", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    try:
        st.session_state.pages = [] 
        st.session_state.pdf_data = None
        
        with st.status("🪄 Creating magic..."):
            # Step A: Hero Analysis
            base64_img = encode_image(uploaded_file)
            char_res = client.chat.get(
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
                
                # Download image
                img_response = requests.get(url)
                img_bytes = BytesIO(img_response.content)
                
                # Save to UI memory
                st.session_state.pages.append({"text": txt, "url": url})

                # Add to PDF using fpdf2's ability to take BytesIO directly
                pdf.add_page()
                pdf.image(img_bytes, x=10, y=10, w=190)
                pdf.set_y(210) # Move cursor below image
                pdf.set_font("Helvetica", size=12)
                # Ensure text is safe for PDF
                safe_text = txt.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            # Finalize PDF as bytes
            st.session_state.pdf_data = pdf.output()

    except Exception as e:
        st.error(f"Error: {e}")

# 3. Display Results
for i, p in enumerate(st.session_state.pages):
    st.markdown(f"### Page {i+1}")
    st.image(p["url"])
    st.write(p["text"])
    st.divider()

# 4. Download
if st.session_state.pdf_data:
    st.download_button(
        label="📥 Download PDF Story",
        data=st.session_state.pdf_data,
        file_name="story.pdf",
        mime="application/pdf"
    )
