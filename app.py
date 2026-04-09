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
        # 1. Analyze Photo & Convert to Generic Character
        with st.status("🔍 Turning your hero into a storybook character..."):
            base64_image = encode_image(uploaded_file)
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe ONLY the colors of the child's clothing and hair. Then, pick a cute animal (like a bunny or bear) to represent them. Format: 'A [animal] wearing [color] clothes'."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}]
            )
            # Use [0] to avoid the 'list' error
            hero_proxy = char_res.choices[0].message.content

        # 2. Write Story
        with st.status("✍️ Writing the adventure..."):
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page story about {hero_proxy}. Format each page exactly like this: Page X: [text] | [image prompt]"}]
            )
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
                
                with st.spinner(f"Painting page {i+1}..."):
                    # We add "Hand-drawn cartoon" and "Fictional" to stay safe
                    safe_art_prompt = f"Whimsical hand-drawn 2D cartoon illustration. Character: {hero_proxy}. Action: {p_prompt}. No real people, no photos, simple colors."
                    
                    img_gen = client.images.generate(
                        model="dall-e-3",
                        prompt=safe_art_prompt,
                        n=1, size="1024x1024"
                    )
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
        st.success("Your story is ready!")
        pdf_output = pdf.output(dest='S')
        st.download_button(
            label="📥 Download PDF", 
            data=bytes(pdf_output), 
            file_name="story.pdf", 
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Error: {e}")
