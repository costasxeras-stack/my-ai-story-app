import streamlit as st
import openai
import base64
from fpdf import FPDF
import io

st.set_page_config(page_title="Bedtime Story AI", page_icon="🌙")
st.title("🌙 Bedtime Story Creator")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key in Secrets!")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

uploaded_file = st.file_uploader("Upload a photo", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    try:
        # 1. Simplify the Hero (Prevents irrelevant images)
        with st.status("🔍 Analyzing hero..."):
            base64_image = encode_image(uploaded_file)
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe the child's hair color and shirt color only. Example: 'blonde hair and blue shirt'."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}]
            )
            hero_style = char_res.choices[0].message.content

        # 2. Write the Story
        with st.status("✍️ Writing pages..."):
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page story about a hero with {hero_style}. Format: Page X: [text] | [short scene description]"}]
            )
            raw_story = story_res.choices[0].message.content
            story_lines = [line for line in raw_story.split('\n') if '|' in line]

        # 3. Create Digital Book
        pdf = FPDF()
        
        for i, line in enumerate(story_lines[:5]):
            parts = line.split('|')
            p_text = parts[0].strip()
            p_scene = parts[1].strip()

            with st.container():
                st.markdown(f"### Page {i+1}")
                with st.spinner(f"Painting page {i+1}..."):
                    # Use a 'Style Anchor' (Watercolor) to keep images relevant
                    img_gen = client.images.generate(
                        model="dall-e-3",
                        prompt=f"Children's book watercolor: A hero with {hero_style} in a {p_scene}.",
                        n=1, size="1024x1024"
                    )
                    st.image(img_gen.data[0].url)
                st.write(p_text)
                st.divider()

                # Add to PDF with safe encoding
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                # FIX: .encode('latin-1', 'replace').decode('latin-1') handles weird AI characters
                safe_text = p_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

        # 4. Final Download (Fixed Encoding Error)
        st.success("Story is ready!")
        
        # FIX: We use a binary stream instead of the bytes() function to avoid encoding errors
        pdf_stream = io.BytesIO()
        pdf_content = pdf.output(dest='S')
        if isinstance(pdf_content, str):
            pdf_content = pdf_content.encode('latin-1')
        pdf_stream.write(pdf_content)
        
        st.download_button(
            label="📥 Download PDF",
            data=pdf_stream.getvalue(),
            file_name="bedtime_story.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Error: {e}")
