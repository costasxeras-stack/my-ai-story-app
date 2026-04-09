import streamlit as st
import openai
import base64
from fpdf import FPDF
import requests
from io import BytesIO

st.set_page_config(page_title="Bedtime Story AI", page_icon="🌙")
st.title("🌙 Bedtime Story Creator")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize "Memory" (Session State) so the story doesn't disappear
if "story_data" not in st.session_state:
    st.session_state.story_data = []
if "pdf_ready" not in st.session_state:
    st.session_state.pdf_ready = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

uploaded_file = st.file_uploader("Upload photo of hero", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    try:
        st.session_state.story_data = [] # Reset for new story
        
        with st.status("🪄 Creating magic..."):
            # 1. Analyze Hero
            base64_image = encode_image(uploaded_file)
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [{"type": "text", "text": "Describe the shirt color and pick a cute woodland animal. Return: 'A [animal] in a [color] shirt'."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
            )
            hero_proxy = char_res.choices[0].message.content

            # 2. Write Story
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page story about {hero_proxy}. Use 'BREAK' between pages."}]
            )
            raw_text = story_res.choices[0].message.content
            pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

            # 3. Process Pages
            pdf = FPDF()
            for i, page_text in enumerate(pages):
                # Generate Image
                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Watercolor illustration: {hero_proxy} in {page_text[:100]}. No humans.",
                    n=1, size="1024x1024"
                )
                img_url = img_gen.data[0].url
                
                # Download image for PDF
                img_data = requests.get(img_url).content
                img_stream = BytesIO(img_data)
                
                # Store in memory
                st.session_state.story_data.append({"text": page_text, "url": img_url})

                # Build PDF Page
                pdf.add_page()
                pdf.image(img_stream, x=10, y=10, w=190)
                pdf.ln(200) # Move text below image
                pdf.set_font("Helvetica", size=12)
                pdf.multi_cell(0, 10, txt=page_text.encode('latin-1', 'replace').decode('latin-1'))

            st.session_state.pdf_ready = pdf.output(dest='S')

    except Exception as e:
        st.error(f"Error: {e}")

# Display the story from memory (so it stays visible)
for i, item in enumerate(st.session_state.story_data):
    st.markdown(f"### Page {i+1}")
    st.image(item["url"])
    st.write(item["text"])
    st.divider()

# Download Button
if st.session_state.pdf_ready:
    pdf_bytes = st.session_state.pdf_ready
    if isinstance(pdf_bytes, str): pdf_bytes = pdf_bytes.encode('latin-1')
    
    st.download_button("📥 Download PDF with Photos", data=pdf_bytes, file_name="story.pdf", mime="application/pdf")

