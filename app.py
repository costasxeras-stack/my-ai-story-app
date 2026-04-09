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
        # 1. Analyze Hero
        with st.status("🔍 Analyzing hero..."):
            base64_image = encode_image(uploaded_file)
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe child hair and shirt color only. Example: 'blonde hair and blue shirt'."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}]
            )
            hero_style = char_res.choices.message.content

        # 2. Write Story - More flexible instructions
        with st.status("✍️ Writing pages..."):
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a short 5-page story about a hero with {hero_style}. For each page, write ONE paragraph followed by a '|' and then a one-sentence image description."}]
            )
            raw_text = story_res.choices.message.content
            # Universal Splitter: Clean up and find any line with a pipe '|'
            story_lines = [line.strip() for line in raw_text.split('\n') if '|' in line and len(line) > 5]
            
            # Fallback: If AI fails to use '|', just take the first 5 non-empty paragraphs
            if not story_lines:
                story_lines = [line.strip() + " | A magical forest" for line in raw_text.split('\n') if len(line) > 20][:5]

        # 3. Create Book
        pdf = FPDF()
        for i, line in enumerate(story_lines):
            parts = line.split('|')
            p_text = parts[0].replace('Page ' + str(i+1) + ':', '').strip()
            p_scene = parts[1].strip() if len(parts) > 1 else "A magical background"

            # Display on UI
            st.markdown(f"### Page {i+1}")
            with st.spinner(f"Painting page {i+1}..."):
                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Children's book watercolor: A hero with {hero_style} in a {p_scene}. No text in image.",
                    n=1, size="1024x1024"
                )
                st.image(img_gen.data[0].url)
            st.write(p_text)
            st.divider()

            # Write to PDF
            pdf.add_page()
            pdf.set_font("Helvetica", size=12) # Use Helvetica for better compatibility
            # Fix white page issue: ensure characters are safe
            safe_text = p_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, txt=safe_text)

        # 4. Final Export
        st.success("Story is ready!")
        pdf_content = pdf.output(dest='S')
        # In some versions of FPDF, output('S') returns bytes, in others it's a string
        if isinstance(pdf_content, str):
            pdf_content = pdf_content.encode('latin-1', 'replace')
            
        st.download_button(
            label="📥 Download PDF",
            data=pdf_content,
            file_name="story.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Error: {e}")
