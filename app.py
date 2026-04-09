import streamlit as st
import openai
import base64
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Magic Bedtime Story", page_icon="🪄")
st.title("🪄 Magic Bedtime Story")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing API Key! Please add it to Streamlit Secrets.")
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "pages" not in st.session_state:
    st.session_state.pages = []
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

uploaded_file = st.file_uploader("1. Upload child's photo", type=['jpg', 'png', 'jpeg'])
room_details = st.text_input("2. What toys/items are in the room? (e.g. blue truck, teddy, stars)", "a teddy bear and stars")

if uploaded_file and st.button("Generate Story"):
    try:
        st.session_state.pages = []
        
        with st.status("🔮 Weaving your story..."):
            # We use the text description to drive the story, keeping the photo safe
            story_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Write a 5-page bedtime story about a child in a room with {room_details}. Make the objects come to life. Use 'BREAK' between pages."}]
            )
            raw_text = story_res.choices.message.content
            raw_pages = [p.strip() for p in raw_text.split('BREAK') if len(p.strip()) > 10][:5]

            pdf = FPDF()
            img_data = uploaded_file.getvalue()

            for i, txt in enumerate(raw_pages):
                st.session_state.pages.append({"text": txt})
                pdf.add_page()
                pdf.image(BytesIO(img_data), x=10, y=10, w=190)
                pdf.set_y(160) 
                pdf.set_font("Helvetica", size=12)
                # Ensure no blank pages by cleaning the AI text
                safe_text = txt.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)

            st.session_state.pdf_bytes = bytes(pdf.output())

    except Exception as e:
        st.error(f"Error: {e}")

# Display the Story on Screen
for i, p in enumerate(st.session_state.pages):
    st.markdown(f"### Page {i+1}")
    st.image(uploaded_file, use_container_width=True)
    st.write(p["text"])
    st.divider()

if st.session_state.pdf_bytes:
    st.download_button("📥 Download PDF", data=st.session_state.pdf_bytes, file_name="story.pdf", mime="application/pdf")
