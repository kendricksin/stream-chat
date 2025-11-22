import streamlit as st
from chat_client import ChatClient
import os
import hashlib
import time
import logging
import tempfile
import json
from pdf_parser_v2 import extract_text_from_pdf, parse_document

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state
if "chat_client" not in st.session_state:
    st.session_state.chat_client = ChatClient()

if "session_id" not in st.session_state:
    st.session_state.session_id = st.session_state.chat_client.session_id

# Check if session was reset (page refresh)
if st.session_state.session_id != st.session_state.chat_client.session_id:
    st.session_state.chat_client = ChatClient()
    st.session_state.session_id = st.session_state.chat_client.session_id

# Set page config
st.set_page_config(
    page_title="Streamlit Chatbot",
    page_icon="🤖",
    layout="wide"
)

def main():
    st.title("🤖 Streamlit Chatbot with PDF Knowledge Base")

    # Check API keys
    api_key = os.getenv("API_KEY")
    
    # Sidebar for configuration and PDF upload
    with st.sidebar:
        st.header("Configuration")
        
        # API configuration check
        if not api_key:
            st.error("API key not configured. Please set API_KEY in your .env file.")
            st.stop()

        st.info(f"Using API: {os.getenv('BASE_URL', 'DashScope')}")
        
        # Show question counter
        question_count = st.session_state.chat_client.get_question_count()
        max_questions = st.session_state.chat_client.get_max_questions()
        st.metric("Questions Used", f"{question_count}/{max_questions}")
        
        if question_count >= max_questions:
            st.warning("Session limit reached! Upload a new PDF to start a new session.")
        
        # Debug toggle
        debug_mode = st.checkbox("Debug Mode", value=False)
        
        st.header("PDF Knowledge Base")
        uploaded_file = st.file_uploader(
            "Upload a PDF file",
            type=["pdf"],
            help="Upload a PDF file to use as reference for Q&A"
        )
        
        parsed_document = None
        if uploaded_file is not None:
            # Check if this is a new file (different from what's already processed)
            file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
            if "last_processed_file_hash" not in st.session_state or st.session_state.last_processed_file_hash != file_hash:
                with st.spinner("Extracting text from PDF..."):
                    try:
                        # Save uploaded file to temporary location
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_file_path = tmp_file.name
                        
                        # Process PDF using parser
                        text = extract_text_from_pdf(tmp_file_path)
                        parsed_document = parse_document(text)
                        
                        # Store parsed document in session state
                        st.session_state.parsed_document = parsed_document
                        st.session_state.last_processed_file_hash = file_hash
                        
                        # Initialize selected sections in session state
                        default_sections = ["2", "4", "5", "6"]
                        st.session_state.selected_sections = default_sections
                        
                        # Automatically add default sections to knowledge base
                        selected_sections = [
                            section for section in st.session_state.parsed_document["sections"]
                            if section["section_number"] in st.session_state.selected_sections
                        ]
                        
                        st.session_state.chat_client.add_structured_knowledge(selected_sections, "PDF")
                        
                        # Clean up temp file
                        os.unlink(tmp_file_path)
                        
                        st.success("PDF processed and default sections added to knowledge base!")
                    except Exception as e:
                        st.error(f"Error processing PDF: {str(e)}")
            else:
                st.info("PDF already processed. Using existing data.")
        
        # If we have a parsed document, show section selector button
        if "parsed_document" in st.session_state and st.session_state.parsed_document:
            # Check if the parsed document has sections
            if "sections" in st.session_state.parsed_document and st.session_state.parsed_document["sections"]:
                if st.button("Select Sections to Include"):
                    st.session_state.show_section_selector = not st.session_state.get("show_section_selector", False)
                    st.rerun()
                
                # Show section selector if requested
                if st.session_state.get("show_section_selector", False):
                    st.subheader("Select Sections")
                    st.info("Choose which sections to include in the knowledge base:")
                    
                    # Initialize selected sections in session state if not exists
                    if "selected_sections" not in st.session_state:
                        st.session_state.selected_sections = ["2", "4", "5", "6"]  # Default selections
                    
                    # Create buttons for each section in a single column
                    for section in st.session_state.parsed_document["sections"]:
                        section_number = section['section_number']
                        section_label = f"{section_number}. {section['title']}"
                        
                        # Determine if section is selected
                        is_selected = section_number in st.session_state.selected_sections
                        
                        # Create button with color based on selection state
                        if is_selected:
                            # Use st.form to handle button clicks without page refresh issues
                            if st.button(section_label, key=f"section_{section_number}", type="primary", use_container_width=True):
                                # Remove from selected sections
                                st.session_state.selected_sections.remove(section_number)
                                st.rerun()
                        else:
                            if st.button(section_label, key=f"section_{section_number}", use_container_width=True):
                                # Add to selected sections
                                st.session_state.selected_sections.append(section_number)
                                st.rerun()
                    
                    # Show selected sections count
                    st.write(f"Selected {len(st.session_state.selected_sections)} sections")
                    
                    # Button to add selected sections to knowledge base
                    if st.button("Update Knowledge Base with Selected Sections"):
                        with st.spinner("Updating knowledge base..."):
                            try:
                                # Filter sections based on selection
                                selected_sections = [
                                    section for section in st.session_state.parsed_document["sections"]
                                    if section["section_number"] in st.session_state.selected_sections
                                ]
                                
                                # Clear existing knowledge base and add new sections
                                st.session_state.chat_client.knowledge_base = []
                                st.session_state.chat_client.add_structured_knowledge(selected_sections, "PDF")
                                st.success(f"Knowledge base updated with {len(selected_sections)} sections!")
                                
                                # Reset session if it was at limit
                                if st.session_state.chat_client.get_question_count() >= st.session_state.chat_client.get_max_questions():
                                    st.session_state.chat_client.reset_session()
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error updating sections: {str(e)}")
        
        # Show current knowledge base info
        if st.session_state.chat_client.knowledge_base:
            st.info(f"Knowledge base with {len(st.session_state.chat_client.knowledge_base)} item(s) loaded")
        
        st.divider()
        
        if st.button("Reset Session"):
            st.session_state.chat_client.reset_session()
            if "parsed_document" in st.session_state:
                del st.session_state.parsed_document
            if "selected_sections" in st.session_state:
                del st.session_state.selected_sections
            if "show_section_selector" in st.session_state:
                del st.session_state.show_section_selector
            st.rerun()
    
    # Debug information
    if debug_mode:
        with st.expander("Debug Information"):
            st.write("Session ID:", st.session_state.session_id)
            st.write("Conversation History:", st.session_state.chat_client.conversation_history)
            st.write("Knowledge Base:", st.session_state.chat_client.knowledge_base)
            st.write("Model:", os.getenv("DEFAULT_MODEL", "qwen3-max"))
            st.write("Base URL:", os.getenv("BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"))
            st.write("Question Count:", st.session_state.chat_client.get_question_count())
            if "selected_sections" in st.session_state:
                st.write("Selected Sections:", st.session_state.selected_sections)
            if "parsed_document" in st.session_state:
                st.write("Parsed Document Structure:", json.dumps(st.session_state.parsed_document, indent=2, ensure_ascii=False))
    
    # Main chat interface
    st.subheader("Chat")

    # Always show suggested questions at the top
    st.info("You can ask questions about the e-bidding document. Here are some suggested questions:")

    # Paired Thai and English questions
    question_pairs = [
        ("คุณสมบัติหลักของผู้ยื่นข้อเสนอ/ผู้เข้าร่วมประมูล มีอะไรบ้าง? (สรุป)", "What are the main qualifications of bidders/participants? (Summarized)"),
        ("ผู้ยื่นข้อเสนอต้องแสดงหลักฐานทางการเงิน / หลักประกันการเสนอราคาเป็นจำนวนเท่าใด?", "How much financial proof / bid security must be provided?"),
        ("หลักประกันการเสนอราคา / หลักฐานทางการเงินที่ยอมรับมีรูปแบบใดบ้าง?", "What are acceptable form of financial proof / bid security?"),
        ("ผู้ยื่นข้อเสนอต้องมีผลงานหรือประสบการณ์ย้อนหลังกี่ปี?", "How many years of company background work or experience are required?"),
        ("การตัดสินผู้ชนะพิจารณาจากราคาต่ำสุดหรือเกณฑ์การให้คะแนน?", "Is the winner determined by lowest price or scoring criteria?")
    ]

    # Create columns for Thai and English questions
    cols = st.columns(2)

    # Thai questions in the left column
    with cols[0]:
        st.subheader("คำถามภาษาไทย")
        for thai_q, english_q in question_pairs:
            if st.button(thai_q, key=f"thai_{hash(thai_q)}", use_container_width=True):
                # Instead of processing directly, populate the chat input
                st.session_state.pending_question = thai_q
                st.session_state.pending_language = "thai"
                st.rerun()

    # English questions in the right column
    with cols[1]:
        st.subheader("English Questions")
        for thai_q, english_q in question_pairs:
            if st.button(english_q, key=f"english_{hash(english_q)}", use_container_width=True):
                # Instead of processing directly, populate the chat input
                st.session_state.pending_question = english_q
                st.session_state.pending_language = "english"
                st.rerun()

    # Display chat history
    for message in st.session_state.chat_client.conversation_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Check if session limit is reached
    is_session_limited = st.session_state.chat_client.get_question_count() >= st.session_state.chat_client.get_max_questions()
    if is_session_limited:
        st.info("Session limit reached. Please upload a new PDF to start a new session.")

    # Always render chat input at the bottom
    prompt = st.chat_input(
        "What would you like to know?",
        disabled=is_session_limited
    )

    # Check if there's a pending question from suggested questions
    language = "english"  # Default language
    if "pending_question" in st.session_state:
        prompt = st.session_state.pending_question
        language = st.session_state.get("pending_language", "english")
        del st.session_state.pending_question
        if "pending_language" in st.session_state:
            del st.session_state.pending_language

    # Process the question if one is provided
    if prompt:
        process_question(prompt, api_key, language)

def process_question(prompt, api_key, language="english"):
    """Process a question and generate a response"""
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # Use configured API
            if not api_key:
                st.error("API key not configured. Please set API_KEY in your .env file.")
                st.stop()

            logger.info(f"Sending message to API: {prompt}")
            stream = st.session_state.chat_client.chat_with_dashscope(prompt, language=language)
            
            # Stream the response
            for chunk in stream:
                logger.debug(f"Received chunk from client: {repr(chunk)}")
                # Check if there's an error in the chunk
                if isinstance(chunk, str) and chunk.startswith("Error:"):
                    if "404" in chunk:
                        st.error("Model or endpoint not found. Please check your model name and API configuration.")
                        st.error("Make sure your model is available in your DashScope account.")
                    else:
                        st.error(chunk)
                    break
                elif isinstance(chunk, str) and chunk.startswith("Session limit reached"):
                    st.info(chunk)
                    break
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
                # Force UI to update immediately
                time.sleep(0.01)
            
            # Final update
            message_placeholder.markdown(full_response)
            logger.info(f"Completed response. Total length: {len(full_response)}")
            
            # If this was the last question, show a message and reset
            if st.session_state.chat_client.get_question_count() >= st.session_state.chat_client.get_max_questions():
                st.info("Session limit reached. Please upload a new PDF to start a new session.")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            st.error(error_msg)

if __name__ == "__main__":
    main()