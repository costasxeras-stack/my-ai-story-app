import streamlit as st
import openai
from fpdf import FPDF
from io import BytesIO

# 1. Setup
st.set_page_config(page_title="Magic Bedtime Story", page_icon="🌙")
st.title("🌙 Magic Bedtime Story")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Memory to keep story on screen
if "story" not in st.session_state:
    st.session_state.story = []
if "pdf" not in st.session_state:
    st.session_state.pdf = None

# 2. Input Fields
uploaded_file = st.file_uploader("1. Upload child's photo", type=['jpg', 'png', 'jpeg'])
hero_name = st.text_input("2. Child's Name", "Leo")
objects = st.text_input("3. What magic items are in the room? (e.g., a blue truck, a teddy, stars)", "a golden star")

if uploaded_file and st.button("Create My Story"):
    try:
        st.session_state.story = []
        
        with st.status("🪄 Weaving your story..."):
            # We use the text input to drive the story, keeping the photo safe on the screen
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Write a 5-page bedtime story about {hero_name} in a room where {objects} come to life. Put 'BREAK' between pages."}]
            )
            
            # Use [0] to fix the 'list' error forever
            full_text = response.choices[0].message.content
            pages = [p.strip() for p in full_text.split('BREAK') if len(p.strip()) > 5][:5]

            # Build the PDF
            pdf = FPDF()
            img_data = uploaded_file.getvalue()

            # First Page with Photo
            pdf.add_page()
            pdf.image(BytesIO(img_data), x=10, y=10, w=190)
            pdf.ln(160) 
            
            for page_text in pages:
                st.session_state.story.append(page_text)
                # Subsequent pages have text only
                if len(st.session_state.story) > 1:
                    pdf.add_page()
                
                pdf.set_font("Helvetica", size=12)
                safe_text = page_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            st.session_state.pdf = bytes(pdf.output())

    except Exception as e:
        st.error(f"Error: {e}")

# 3. Show Result
if uploaded_file:
    st.image(uploaded_file, caption="Our Hero", use_container_width=True)

for i, text in enumerate(st.session_state.story):
    st.markdown(f"### Chapter {i+1}")
    st.write(text)
    st.divider()

# 4. Download
if st.session_state.pdf:
    st.download_button("📥 Download PDF Story", data=st.session_state.pdf, file_name="story.pdf")
