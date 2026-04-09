import streamlit as st
import openai
import base64
from fpdf import FPDF
import requests
from io import BytesIO

# 1. Page Configuration
st.set_page_config(page_title="Bedtime Story AI", page_icon="🌙")
st.title("🌙 Bedtime Story Creator")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Please add OPENAI_API_KEY to your Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize Session State
if "story_pages" not in st.session_state:
    st.session_state.story_pages = []
if "final_pdf" not in st.session_state:
    st.session_state.final_pdf = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. User Interface
uploaded_file = st.file_uploader("Upload photo of hero", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    try:
        # Reset memory for new generation
        st.session_state.story_pages = []
        st.session_state.final_pdf = None
        
        with st.status("🪄 Creating magic... (This takes ~2 mins)"):
            # Step A: Analyze Hero (Using .create, NOT .get)
            base64_img = encode_image(uploaded_file)
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe the shirt color and pick a woodland animal. Return ONLY: 'A [animal] in a [color] shirt'."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                ]}]
            )
            hero_proxy = char_res.choices[0].message.content

            # Step B: Write Story
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page story about {hero_proxy}. Use 'BREAK' between pages."}]
            )
            raw_text = story_res.choices[0].message.content
            page_texts = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

            # Step C: Build Story and PDF
            pdf = FPDF()
            for i, txt in enumerate(page_texts):
                # Image Generation
                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Watercolor illustration: {hero_proxy} in {txt[:100]}. No humans.",
                    n=1, size="1024x1024"
                )
                img_url = img_gen.data[0].url
                
                # Fetch Image for PDF
                img_resp = requests.get(img_url)
                img_bytes = BytesIO(img_resp.content)
                
                # Save to UI memory
                st.session_state.story_pages.append({"text": txt, "url": img_url})

                # Add to PDF (fpdf2 handles BytesIO)
                pdf.add_page()
                pdf.image(img_bytes, x=10, y=10, w=190)
                pdf.set_y(210)
                pdf.set_font("Helvetica", size=12)
                safe_text = txt.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            # Finalize PDF
            st.session_state.final_pdf = pdf.output()

    except Exception as e:
        st.error(f"Error: {e}")

# 3. Display Results
for i, p in enumerate(st.session_state.story_pages):
    st.markdown(f"### Page {i+1}")
    st.image(p["url"])
    st.write(p["text"])
    st.divider()

# 4. Final Download Button
if st.session_state.final_pdf:
    st.download_button(
        label="📥 Download PDF with Photos",
        data=st.session_state.final_pdf,
        file_name="storybook.pdf",
        mime="application/pdf"
    )
