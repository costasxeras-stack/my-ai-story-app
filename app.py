import streamlit as st
import openai
import json
import base64
from fpdf import FPDF

# 1. Setup
st.set_page_config(page_title="Bedtime Story AI", page_icon="🌙")
st.title("🌙 Bedtime Story Creator")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Please add your API key to Streamlit Secrets!")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Input
uploaded_file = st.file_uploader("Upload a photo", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    with st.status("🪄 Creating magic... (This takes 2 minutes)"):
        try:
            # STEP A: Analyze Image - Keep it very generic for safety
            st.write("🔍 Identifying our hero...")
            base64_image = encode_image(uploaded_file)
            
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe the child's hair color and outfit only. Do not mention their face or names. Example: 'A child with blonde hair wearing a blue shirt'."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}]
            )
            hero_desc = char_res.choices[0].message.content

            # STEP B: Generate Story
            st.write("✍️ Writing 5 magical pages...")
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page story about a hero with these traits: {hero_desc}. Format exactly: Page 1: [text] | [image prompt]..."}]
            )
            raw_story = story_res.choices[0].message.content
            story_lines = [line for line in raw_story.split('\n') if '|' in line]

            # STEP C: Images & PDF
            pdf = FPDF()
            for i, line in enumerate(story_lines[:5]):
                st.write(f"🎨 Painting illustration {i+1} of 5...")
                
                parts = line.split('|')
                page_text = parts[0].strip()
                image_prompt = parts[1].strip()

                # SAFETY FIX: We strictly define this as a "Whimsical Storybook Character" 
                # and remove any link to the real photo.
                safe_prompt = f"A whimsical, 2D watercolor children's book illustration of a generic storybook character with {hero_desc}. Setting: {image_prompt}. No realistic faces, no photos."

                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=safe_prompt,
                    n=1, size="1024x1024"
                )
                img_url = img_gen.data[0].url 
                
                st.image(img_url, caption=f"Page {i+1}")
                st.write(page_text)
                
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, txt=page_text.encode('latin-1', 'replace').decode('latin-1'))

            # STEP D: Download
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Download PDF", pdf_bytes, "story.pdf", "application/pdf")
            st.success("Your magical story is ready!")

        except Exception as e:
            st.error(f"Error: {e}")
