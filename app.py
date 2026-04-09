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
uploaded_file = st.file_uploader("Upload a photo", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    try:
        # STEP A: Analyze Photo
        with st.status("🔍 Analyzing hero..."):
            base64_image = encode_image(uploaded_file)
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe the child's hair and shirt color only. Example: 'brown hair and a red sweater'."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}]
            )
            # FIX: Added [0] here
            hero_style = char_res.choices[0].message.content

        # STEP B: Write Story
        with st.status("✍️ Writing pages..."):
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page story about a hero with {hero_style}. Format every page exactly as: Page X: [text] | [image prompt]"}]
            )
            # FIX: Added [0] here
            raw_text = story_res.choices[0].message.content
            story_lines = [line.strip() for line in raw_text.split('\n') if '|' in line]

        # STEP C: Display & PDF
        pdf = FPDF()
        for i, line in enumerate(story_lines[:5]):
            parts = line.split('|')
            p_text = parts[0].strip()
            p_scene = parts[1].strip() if len(parts) > 1 else "A magical forest"

            st.markdown(f"### Page {i+1}")
            with st.spinner(f"Painting page {i+1}..."):
                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Children's book watercolor illustration, simple style: A hero with {hero_style} in a {p_scene}. No text.",
                    n=1, size="1024x1024"
                )
                # FIX: Added [0] here
                img_url = img_gen.data[0].url
                st.image(img_url)
            st.write(p_text)
            st.divider()

            # Add to PDF
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            safe_text = p_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, txt=safe_text)

        # STEP D: Final Download
        st.success("Success!")
        pdf_output = pdf.output(dest='S')
        # Handle string vs bytes output
        if isinstance(pdf_output, str):
            pdf_output = pdf_output.encode('latin-1')

        st.download_button(
            label="📥 Download PDF",
            data=pdf_output,
            file_name="story.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Final Error: {e}")
