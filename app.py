import streamlit as st
import openai
import base64
from fpdf import FPDF

st.set_page_config(page_title="Bedtime Story AI", page_icon="🌙")
st.title("🌙 Bedtime Story Creator")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key in Secrets!")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

uploaded_file = st.file_uploader("Upload a photo of the hero", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    try:
        # 1. Analyze Photo
        with st.status("🔍 Identifying hero..."):
            base64_image = encode_image(uploaded_file)
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe the child's hair and outfit only. No names."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}]
            )
            # FIXED: Added [0] here
            hero_desc = char_res.choices[0].message.content

        # 2. Write Story
        with st.status("✍️ Writing pages..."):
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page story about a hero: {hero_desc}. Format: Page X: [text] | [prompt]"}]
            )
            # FIXED: Added [0] here
            raw_story = story_res.choices[0].message.content
            story_lines = [line for line in raw_story.split('\n') if '|' in line]

        # 3. Display Story & Prepare PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        for i, line in enumerate(story_lines[:5]):
            parts = line.split('|')
            p_text = parts[0].strip()
            p_prompt = parts[1].strip()

            with st.container():
                st.markdown(f"### Page {i+1}")
                
                with st.spinner(f"Painting illustration {i+1}..."):
                    img_gen = client.images.generate(
                        model="dall-e-3",
                        prompt=f"Watercolor children's book style: {p_prompt}. Character: {hero_desc}",
                        n=1, size="1024x1024"
                    )
                    # FIXED: Added [0] here
                    img_url = img_gen.data[0].url
                    st.image(img_url)
                
                st.write(p_text)
                st.divider()

                # Add to PDF
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, f"Page {i+1}", ln=True, align='C')
                pdf.ln(5)
                pdf.set_font("Arial", size=12)
                clean_text = p_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=clean_text)

        # 4. Final Download Button
        st.success("The story is complete!")
        pdf_output = pdf.output(dest='S')
        st.download_button(
            label="📥 Download this story as a PDF", 
            data=bytes(pdf_output), 
            file_name="bedtime_story.pdf", 
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Something went wrong: {e}")
