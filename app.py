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
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Please configure the OpenAI API Key in Streamlit Secrets.")
    st.stop()

# 3. Helper Functions
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 4. User Input
uploaded_file = st.file_uploader("Upload a photo of the hero (your child)", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    with st.status("🪄 Creating magic..."):
        try:
            # Step A: Analyze Image & Create JSON Character
            base64_image = encode_image(uploaded_file)
            
            st.write("Analyzing hero...")
            char_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this photo and return ONLY a JSON object with 'name', 'hair_color', 'outfit', and 'personality'. No markdown, no explanations."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }],
                response_format={"type": "json_object"}
            )
            character = json.loads(char_response.choices[0].message.content)

            # Step B: Generate Story, Prompts, and Narration
            st.write("Writing 5-page story...")
            story_prompt = f"Write a 5-page bedtime story about {character['name']}. For each page, provide: 1) Story text, 2) A detailed DALL-E image prompt, 3) Short narration. Return ONLY JSON with a list of 5 objects containing 'page_text', 'image_prompt', 'narration'. No markdown."
            
            story_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": story_prompt}],
                response_format={"type": "json_object"}
            )
            story_data = json.loads(story_response.choices[0].message.content)['pages']

            # Step C: Generate Images & Build PDF
            pdf = FPDF()
            
            for i, page in enumerate(story_data):
                st.write(f"Generating illustration for page {i+1}...")
                
                # Image Generation
                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Whimsical children's book illustration: {page['image_prompt']}. Character description: {character['outfit']}, {character['hair_color']}.",
                    n=1, size="1024x1024"
                )
                img_url = img_gen.data[0].url
                
                # Display to User
                st.image(img_url, caption=f"Page {i+1}")
                st.write(page['page_text'])
                
                # Add to PDF
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, txt=page['page_text'])

            # Step D: Download PDF
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(label="📥 Download PDF Story", data=pdf_output, file_name="bedtime_story.pdf", mime="application/pdf")
            st.success("Story Complete!")

        except Exception as e:
            st.error(f"An error occurred: {e}")
