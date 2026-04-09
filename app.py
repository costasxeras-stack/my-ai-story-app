import streamlit as st
import openai
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Magic Bedtime Story", page_icon="🌙")
st.title("🌙 Magic Bedtime Story")

# 1. Setup
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "story" not in st.session_state:
    st.session_state.story = []
if "pdf" not in st.session_state:
    st.session_state.pdf = None

# 2. Inputs (The "Human" Vision)
uploaded_file = st.file_uploader("1. Upload child's photo", type=['jpg', 'png', 'jpeg'])
hero_name = st.text_input("2. Child's Name", "Leo")
magic_items = st.text_input("3. What's in the room? (e.g. blue blanket, teddy, stars)", "a soft blanket and a toy bear")

if uploaded_file and st.button("Create My Story"):
    try:
        st.session_state.story = []
        
        with st.status("🪄 Weaving the magic..."):
            # We use GPT-4o-mini (cheaper and faster) since we aren't using vision
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Write a 5-page story about {hero_name} in a room where {magic_items} come to life. Put 'BREAK' between pages."}]
            )
            
            # The 'choices[0]' fix for the list error
            full_text = response.choices[0].message.content
            pages = [p.strip() for p in full_text.split('BREAK') if len(p.strip()) > 5][:5]

            # Build the PDF
            pdf = FPDF()
            img_data = uploaded_file.getvalue()

            # First Page with Photo
            pdf.add_page()
            pdf.image(BytesIO(img_data), x=10, y=10, w=190)
            pdf.ln(160) 
            
            for text in pages:
                st.session_state.story.append(text)
                if len(st.session_state.story) > 1:
                    pdf.add_page()
                
                pdf.set_font("Helvetica", size=12)
                safe_text = text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            st.session_state.pdf = bytes(pdf.output())

    except Exception as e:
        st.error(f"Error: {e}")

# 3. Show Results
if uploaded_file:
    st.image(uploaded_file, caption="Our Hero", use_container_width=True)

for i, txt in enumerate(st.session_state.story):
    st.markdown(f"### Chapter {i+1}")
    st.write(txt)
    st.divider()

# 4. Download
if st.session_state.pdf:
    st.download_button("📥 Download PDF Story", data=st.session_state.pdf, file_name="story.pdf")
