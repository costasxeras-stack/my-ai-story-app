import streamlit as st
import openai
import base64
from fpdf import FPDF
import io

# 1. Setup
st.set_page_config(page_title="Bedtime Story AI", page_icon="🌙")
st.title("🌙 Bedtime Story Creator")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Input
uploaded_file = st.file_uploader("Upload photo of hero", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    try:
        # STEP A: Analyze Hero
        with st.status("🔍 Analyzing hero..."):
            base64_image = encode_image(uploaded_file)
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe the child's hair and outfit colors only. Be brief."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}]
            )
            # FIX: Added [0] to pick the first choice from the list
            hero_style = char_res.choices[0].message.content

        # STEP B: Write Story 
        with st.status("✍️ Writing pages..."):
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page story about a hero with {hero_style}. Put the word 'BREAK' between every page."}]
            )
            # FIX: Added [0] to pick the first choice from the list
            raw_text = story_res.choices[0].message.content
            story_pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

        # STEP C: Generate Images & Build PDF
        pdf = FPDF()
        for i, page_text in enumerate(story_pages):
            st.markdown(f"### Page {i+1}")
            
            with st.spinner(f"Painting illustration {i+1}..."):
                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Children's book watercolor style: {page_text[:300]}. Character traits: {hero_style}.",
                    n=1, size="1024x1024"
                )
                # FIX: Added [0] to pick the first image from the list
                img_url = img_gen.data[0].url
                st.image(img_url)
            
            st.write(page_text)
            st.divider()

            # Add to PDF
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            pdf_safe_text = page_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, txt=pdf_safe_text)

        # STEP D: Final Export
        st.success("Your story is ready!")
        pdf_bytes = pdf.output(dest='S')
        if isinstance(pdf_bytes, str):
            pdf_bytes = pdf_bytes.encode('latin-1')

        st.download_button("📥 Download Final PDF", data=pdf_bytes, file_name="story.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"Error fixed: {e}")
