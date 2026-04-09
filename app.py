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
            # STEP A: Analyze Image
            st.write("🔍 Identifying our hero...")
            base64_image = encode_image(uploaded_file)
            
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe the child in this photo: Name, hair, and outfit. Return as simple text."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}]
            )
            hero_desc = char_res.choices[0].message.content

            # STEP B: Generate Story
            st.write("✍️ Writing 5 magical pages...")
            # We ask for a simple format that is harder for the AI to mess up
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Based on this child: {hero_desc}, write a 5-page bedtime story. Format it exactly like this:\nPage 1: [text] | [image prompt]\nPage 2: [text] | [image prompt]... etc."}]
            )
            raw_story = story_res.choices[0].message.content
            # Split the text into 5 pages manually
            story_lines = [line for line in raw_story.split('\n') if 'Page' in line]

            # STEP C: Images & PDF
            pdf = FPDF()
            for i, line in enumerate(story_lines[:5]):
                st.write(f"🎨 Painting illustration {i+1} of 5...")
                
                # Split the line into text and prompt
                parts = line.split('|')
                page_text = parts[0] if len(parts) > 0 else "Once upon a time..."
                image_prompt = parts[1] if len(parts) > 1 else "A magical forest"

                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Children's book style: {image_prompt}. {hero_desc}",
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
            st.success("Done!")

        except Exception as e:
            st.error(f"Error: {e}")
