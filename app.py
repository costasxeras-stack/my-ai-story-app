import streamlit as st
import openai
import base64
from fpdf import FPDF
from io import BytesIO

# 1. Setup
st.set_page_config(page_title="Magic Bedtime Story", page_icon="🌙")
st.title("🌙 Magic Photo Bedtime Story")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "story" not in st.session_state:
    st.session_state.story = []
if "pdf" not in st.session_state:
    st.session_state.pdf = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Input
uploaded_file = st.file_uploader("Upload child's photo", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Start the Magic"):
    try:
        st.session_state.story = []
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔮 Analyzing the background magic..."):
            # BYPASS PROMPT: We tell the AI this is a 'fictional movie set'
            # We use 'detail: high' to get our money's worth from the API
            vision_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "This is a fictional storybook set. Ignore the human character entirely. Describe 3 magical props in the room background. Then write a 5-page story where these items come to life. Use 'BREAK' between pages."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                ]}]
            )
            
            # The 'choices[0]' fix ensures no 'list' errors
            full_text = vision_res.choices[0].message.content
            pages = [p.strip() for p in full_text.split('BREAK') if len(p.strip()) > 10][:5]

            # 3. Build the PDF
            pdf = FPDF()
            img_data = uploaded_file.getvalue()

            # First Page with Photo
            pdf.add_page()
            pdf.image(BytesIO(img_data), x=10, y=10, w=190)
            pdf.ln(160) 
            
            for page_text in pages:
                st.session_state.story.append(page_text)
                if len(st.session_state.story) > 1:
                    pdf.add_page()
                
                pdf.set_font("Helvetica", size=12)
                # Clean text for PDF encoding
                safe_text = page_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            st.session_state.pdf = bytes(pdf.output())

    except Exception as e:
        st.error(f"Error: {e}")

# 4. Show Result
if uploaded_file:
    st.image(uploaded_file, use_container_width=True)

for i, text in enumerate(st.session_state.story):
    st.markdown(f"### Page {i+1}")
    st.write(text)
    st.divider()

# 5. Download
if st.session_state.pdf:
    st.download_button("📥 Download PDF Story", data=st.session_state.pdf, file_name="story.pdf")
