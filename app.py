import streamlit as st
import openai
import json
import base64
from fpdf import FPDF
from io import BytesIO

# 1. Setup & Page Config
st.set_page_config(page_title="Bedtime Story AI", page_icon="🌙")
st.title("🌙 Bedtime Story Creator")
st.subheader("Turn a photo into a magical 5-page story")

# 2. Get API Key from Secrets
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Please configure the OpenAI API Key in Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 3. Helper Functions
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 4. User Input
uploaded_file = st.file_uploader("Upload a photo of the hero", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    with st.status("🪄 Creating magic... (Takes ~2 mins)"):
        try:
            # Step A: Analyze Image
            base64_image = encode_image(uploaded_file)
            st.write("🔍 Identifying our hero...")
            
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this photo. Return ONLY JSON with: 'name', 'hair', 'outfit'."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }],
                response_format={"type": "json_object"}
            )
            character = json.loads(char_res.choices.message.content)

            # Step B: Generate Story
            st.write("✍️ Writing 5 magical pages...")
            story_prompt = f"Write a 5-page story about {character.get('name', 'the hero')}. Return ONLY a JSON object containing a list named 'pages'. Each page needs 'page_text' and 'image_prompt'."
            
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": story_prompt}],
                response_format={"type": "json_object"}
            )
            
            # THE SAFETY NET: Try to find 'pages' or use whatever list the AI gave us
            raw_data = json.loads(story_res.choices.message.content)
            story_data = raw_data.get('pages') or list(raw_data.values())[0]

            # Step C: Visuals & PDF
            pdf = FPDF()
            for i, page in enumerate(story_data[:5]): # Ensure only 5 pages
                st.write(f"🎨 Painting illustration {i+1} of 5...")
                
                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Children's book style: {page.get('image_prompt', 'magic forest')}",
                    n=1, size="1024x1024"
                )
                img_url = img_gen.data[0].url
                
                st.image(img_url, caption=f"Page {i+1}")
                st.write(page.get('page_text', 'Once upon a time...'))
                
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, txt=page.get('page_text', ''))

            # Step D: Download
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Download PDF Story", pdf_bytes, "story.pdf", "application/pdf")
            st.success("Your story is ready!")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
