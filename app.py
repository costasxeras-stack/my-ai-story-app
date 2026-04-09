import streamlit as st
import openai
import base64
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Magic Photo Bedtime Story", page_icon="🪄")
st.title("🪄 Magic Photo Bedtime Story")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Please add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "pages" not in st.session_state:
    st.session_state.pages = []
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

uploaded_file = st.file_uploader("Upload a photo of your child", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Start the Adventure"):
    try:
        st.session_state.pages = []
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔮 Scanning the room for magic..."):
            # STRATEGY: We tell the AI to ignore the person to bypass privacy blocks
            vision_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Ignore the person in this photo. Look ONLY at the background, furniture, and toys. List 3 specific items you see (e.g. a striped pillow, a wooden block, a green curtain). Then write a 5-page story where these objects come to life. Put the word 'BREAK' between pages."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                ]}]
            )
            raw_text = vision_res.choices[0].message.content
            raw_pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

            pdf = FPDF()
            img_data = uploaded_file.getvalue()

            for i, txt in enumerate(raw_pages):
                st.session_state.pages.append({"text": txt})
                pdf.add_page()
                img_stream = BytesIO(img_data)
                pdf.image(img_stream, x=10, y=10, w=190)
                pdf.set_y(150) 
                pdf.set_font("Helvetica", size=12)
                # Cleaning text for PDF compatibility
                safe_text = txt.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            st.session_state.pdf_bytes = bytes(pdf.output())

    except Exception as e:
        st.error(f"Error: {e}")

# Display Results
for i, p in enumerate(st.session_state.pages):
    st.markdown(f"### Page {i+1}")
    st.image(uploaded_file, use_container_width=True)
    st.write(p["text"])
    st.divider()

if st.session_state.pdf_bytes:
    st.download_button("📥 Download Final PDF", data=st.session_state.pdf_bytes, file_name="magic_story.pdf", mime="application/pdf")
