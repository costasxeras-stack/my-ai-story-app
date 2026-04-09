import streamlit as st
import openai
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Magic Bedtime Story", page_icon="🌙")
st.title("🌙 Magic Bedtime Story")

# 1. Simple Setup
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
adventure = st.text_input("3. What is the adventure? (e.g. Flying to the moon)", "Meeting a friendly dragon")

if uploaded_file and st.button("Create My Story"):
    try:
        st.session_state.story = []
        
        with st.status("🪄 Writing your story..."):
            # Simple AI call that avoids the 'list' error
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Write a 5-page story about {hero_name} {adventure}. Put 'BREAK' between pages."}]
            )
            
            # The "Safe" way to read the response
            full_text = response.choices[0].message.content
            pages = [p.strip() for p in full_text.split('BREAK') if len(p.strip()) > 5][:5]

            # Build the PDF
            pdf = FPDF()
            img_data = uploaded_file.getvalue()

            for i, page_text in enumerate(pages):
                st.session_state.story.append(page_text)
                
                pdf.add_page()
                # Put original photo at top
                pdf.image(BytesIO(img_data), x=10, y=10, w=190)
                pdf.set_y(150) 
                pdf.set_font("Helvetica", size=12)
                # Clean text for PDF
                safe_text = page_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            st.session_state.pdf = bytes(pdf.output())

    except Exception as e:
        st.error(f"Error: {e}")

# 3. Show Story on Screen
for i, text in enumerate(st.session_state.story):
    st.markdown(f"### Page {i+1}")
    st.image(uploaded_file)
    st.write(text)
    st.divider()

# 4. Download
if st.session_state.pdf:
    st.download_button("📥 Download PDF Story", data=st.session_state.pdf, file_name="story.pdf")
