import streamlit as st
import openai
import json
import base64
from fpdf import FPDF
from io import BytesIO

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
                    {"type": "text", "text": "Return ONLY JSON: {'name': '...', 'outfit': '...'}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}],
                response_format={"type": "json_object"}
            )
            # FIXED: Added .content here
            character = json.loads(char_res.choices[0].message.content)
            hero_name = character.get('name', 'the hero')

            # STEP B: Generate Story
            st.write(f"✍️ Writing a story for {hero_name}...")
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page story about {hero_name}. Return ONLY JSON with a list called 'pages'. Each item has 'text' and 'prompt'."}],
                response_format={"type": "json_object"}
            )
            # FIXED: Added .content here
            story_json = json.loads(story_res.choices[0].message.content)
            pages = story_json.get('pages', [])

            # STEP C: Images & PDF
            pdf = FPDF()
            for i, page in enumerate(pages[:5]):
                st.write(f"🎨 Painting illustration {i+1} of 5...")
                
                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Children's book style: {page.get('prompt', 'magical scene')}. Character is {hero_name}.",
                    n=1, size="1024x1024"
                )
                img_url = img_gen.data[0].url # FIXED: Added [0] here
                
                st.image(img_url, caption=f"Page {i+1}")
                st.write(page.get('text', 'Once upon a time...'))
                
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, txt=page.get('text', ''))

            # STEP D: Download
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Download PDF", pdf_bytes, "story.pdf", "application/pdf")
            st.success("Done!")

        except Exception as e:
            st.error(f"Error: {e}")
