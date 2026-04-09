import streamlit as st
import openai
import base64
from fpdf import FPDF
from io import BytesIO

# 1. Setup
st.set_page_config(page_title="Magic Photo Bedtime Story", page_icon="🪄")
st.title("🪄 Magic Photo Bedtime Story")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Please add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize memory so the story stays visible
if "pages" not in st.session_state:
    st.session_state.pages = []
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# 2. Interface
uploaded_file = st.file_uploader("Upload a photo of your child", type=['jpg', 'png', 'jpeg'])

if uploaded_file and st.button("Start the Adventure"):
    try:
        st.session_state.pages = [] # Reset memory
        base64_img = encode_image(uploaded_file)
        
        with st.status("🔮 Analyzing your specific photo..."):
            # We add [0] to the response to fix the 'list' object error
            vision_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Look at THIS specific photo. List 3 actual objects you see. Then write a 5-page bedtime story where these objects come to life around the child. Put the word 'BREAK' between pages."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}", "detail": "high"}}
                ]}]
            )
            # FIX: Added .choices[0] here
            raw_text = vision_res.choices[0].message.content
            raw_pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

            # 3. Create PDF
            pdf = FPDF()
            img_data = uploaded_file.getvalue()

            for i, txt in enumerate(raw_pages):
                st.session_state.pages.append({"text": txt})
                
                pdf.add_page()
                # Use BytesIO to handle the image in memory
                img_stream = BytesIO(img_data)
                pdf.image(img_stream, x=10, y=10, w=190)
                pdf.set_y(150) 
                pdf.set_font("Helvetica", size=12)
                # Ensure characters like smart quotes don't break the PDF
                safe_text = txt.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            # Save PDF to memory
            st.session_state.pdf_bytes = bytes(pdf.output())

    except Exception as e:
        st.error(f"Error: {e}")

# 4. Display Results (This part ensures the story stays on screen)
for i, p in enumerate(st.session_state.pages):
    st.markdown(f"### Page {i+1}")
    st.image(uploaded_file, use_container_width=True)
    st.write(p["text"])
    st.divider()

# 5. Download Button
if st.session_state.pdf_bytes:
    st.download_button(
        label="📥 Download Final PDF", 
        data=st.session_state.pdf_bytes, 
        file_name="magic_story.pdf", 
        mime="application/pdf"
    )
