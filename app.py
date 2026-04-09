import streamlit as st
import openai
import base64
from fpdf import FPDF

st.set_page_config(page_title="Bedtime Story AI", page_icon="🌙")
st.title("🌙 Bedtime Story Creator")

# 1. API Check
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Input
uploaded_file = st.file_uploader("Upload photo of hero", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Generate My Story"):
    try:
        # STEP A: Describe Hero
        with st.status("🔍 Analyzing hero..."):
            base64_image = encode_image(uploaded_file)
            char_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Describe the child's hair and clothing colors only."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}]
            )
            hero_style = char_res.choices.message.content

        # STEP B: Write Story 
        with st.status("✍️ Writing pages..."):
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page story about a hero with {hero_style}. IMPORTANT: Put the word 'BREAK' between every page so I can separate them."}]
            )
            raw_text = story_res.choices.message.content
            # This splits the big block of text into 5 separate pages
            story_pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

        # STEP C: Generate Images & Build PDF
        pdf = FPDF()
        for i, page_text in enumerate(story_pages):
            # 1. SHOW TEXT ON STREAMLIT SCREEN
            st.markdown(f"### Page {i+1}")
            
            with st.spinner(f"Painting illustration {i+1}..."):
                img_gen = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Children's book watercolor illustration: {page_text[:400]}. Hero has {hero_style}.",
                    n=1, size="1024x1024"
                )
                st.image(img_gen.data.url)
            
            # Display the story text on the app screen
            st.write(page_text)
            st.divider()

            # 2. ADD TEXT TO PDF
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            # This 'encoding' line ensures the text actually shows up and isn't a blank/white page
            pdf_safe_text = page_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, txt=pdf_safe_text)

        # STEP D: Export
        st.success("Your story is ready!")
        pdf_bytes = pdf.output(dest='S')
        if isinstance(pdf_bytes, str):
            pdf_bytes = pdf_bytes.encode('latin-1')

        st.download_button("📥 Download Final PDF", data=pdf_bytes, file_name="bedtime_story.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"Error: {e}")
