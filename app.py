import streamlit as st
import openai
import base64
from fpdf import FPDF
import io

st.set_page_config(page_title="Bedtime Story AI", page_icon="🌙")
st.title("🌙 Bedtime Story Creator")

# 1. API Setup
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Upload
uploaded_file = st.file_uploader("Upload photo of hero", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    try:
        # STEP A: Create a 'Proxy' character (Fixes Safety Policy Violations)
        with st.status("🔍 Designing your character..."):
            base64_image = encode_image(uploaded_file)
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe ONLY the shirt color in this photo. Then, pick a cute woodland animal. Return: 'A [animal] in a [color] shirt'."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}]
            )
            # FIX: New attribute-based access to avoid 'not subscriptable'
            hero_proxy = char_res.choices[0].message.content

        # STEP B: Write Story
        with st.status("✍️ Writing pages..."):
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page story about {hero_proxy}. End each page with the word 'BREAK'."}]
            )
            raw_text = story_res.choices[0].message.content
            story_pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

        # STEP C: Generate Images & PDF
        pdf = FPDF()
        for i, page_text in enumerate(story_pages):
            st.markdown(f"### Page {i+1}")
            
            with st.spinner(f"Painting page {i+1}..."):
                # Safety bypass: strictly fictional watercolor style
                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Whimsical watercolor illustration: {hero_proxy} in a {page_text[:100]}. NO humans, only animals.",
                    n=1, size="1024x1024"
                )
                img_url = img_gen.data[0].url
                st.image(img_url)
            
            st.write(page_text)
            st.divider()

            # PDF Construction
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            safe_text = page_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, txt=safe_text)

        # STEP D: Download
        st.success("Your story is ready!")
        pdf_bytes = pdf.output(dest='S')
        if isinstance(pdf_bytes, str):
            pdf_bytes = pdf_bytes.encode('latin-1')

        st.download_button("📥 Download PDF", data=pdf_bytes, file_name="story.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"Final Fix Applied. If error persists, check OpenAI Credits. Error: {e}")
