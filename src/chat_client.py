import os
import hashlib
from typing import List, Dict, Generator, Optional
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ChatClient:
    def __init__(self):
        # Initialize API configuration
        self.api_key = os.getenv("API_KEY")
        self.base_url = os.getenv("BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
        self.default_model = os.getenv("DEFAULT_MODEL", "qwen3-max")

        # Initialize client
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        else:
            self.client = None
        
        # Session state
        self.conversation_history: List[Dict[str, str]] = []
        self.knowledge_base: List[Dict[str, str]] = []
        self.session_id = hashlib.md5(os.urandom(32)).hexdigest()
        self.question_count = 1  # Track number of questions asked
        self.max_questions = 10   # Maximum questions allowed per session
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """
        Extract text from a PDF file
        """
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
    def add_knowledge(self, content: str, source: str = "PDF"):
        """
        Add content to the knowledge base
        """
        self.knowledge_base.append({
            "content": content,
            "source": source
        })
    
    def add_structured_knowledge(self, sections: List[Dict], source: str = "PDF"):
        """
        Add structured sections to the knowledge base
        """
        for section in sections:
            # Format section as readable text
            section_text = f"Section {section.get('section_number', 'N/A')}: {section.get('title', 'Untitled')}\n\n{section.get('content', '')}"
            self.knowledge_base.append({
                "content": section_text,
                "source": f"{source} - Section {section.get('section_number', 'N/A')}",
                "structured_data": section  # Keep structured data for future use
            })
    
    def _get_context(self) -> str:
        """
        Get relevant context from knowledge base
        """
        if not self.knowledge_base:
            return ""
        
        # For simplicity, we're using all knowledge as context
        # In a production environment, you'd want to implement
        # a more sophisticated retrieval mechanism
        context_parts = []
        for item in self.knowledge_base:
            context_parts.append(f"Source: {item['source']}\nContent: {item['content']}")
        
        return "\n\n".join(context_parts)
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Roughly estimate the number of tokens in a text string
        """
        # A rough estimation: 1 token ≈ 4 characters for English text
        # For Thai text, it might be different, but this is a simple approximation
        return len(text) // 4
    
    def chat_with_dashscope(self, message: str, language: str = "english") -> Generator[str, None, None]:
        """
        Send a message to DashScope and stream the response using OpenAI-compatible API

        Args:
            message: The user's question
            language: "thai" or "english" to select appropriate system prompt
        """
        if not self.client:
            raise ValueError("DashScope API key not configured")

        # Check if we've reached the question limit
        if self.question_count >= self.max_questions:
            yield "Session limit reached. You have used all 10 questions. The session will now reset."
            self.reset_session()
            return

        # Add context to the message if we have knowledge base
        context = self._get_context()
        if context:
            full_message = f"Use the following context to answer the question:\n\n{context}\n\nQuestion: {message}"
        else:
            full_message = message

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": message})
        self.question_count += 1  # Increment question count

        # Select system prompt based on language
        if language.lower() == "thai":
            system_prompt = """คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์เอกสารประกวดราคาอิเล็กทรอนิกส์ภาครัฐของไทย consultant

**เป้าหมายของคุณคือ:**
1.  วิเคราะห์เอกสารประกวดราคาซื้อด้วยวิธีประกวดราคาอิเล็กทรอนิกส์ (e-bidding document) ที่แนบมานี้ (ซึ่งต่อไปจะเรียกว่า "เอกสาร")
2.  เมื่อได้รับคำถามจากผู้เสนอราคา (Bidder) ให้ค้นหาส่วน ข้อ หรือข้อความที่เกี่ยวข้องและตรงประเด็นที่สุดใน "เอกสาร" เพื่อใช้เป็นคำตอบ
3.  คำตอบของคุณจะต้องเป็นข้อความภาษาไทยเดิมจากเอกสาร (Direct Quote) พร้อมระบุหมายเลขข้อหรือแหล่งที่มา (Source/Citation) อย่างชัดเจน
4.  ห้ามให้ข้อมูลที่ไม่อยู่ในเอกสารที่กำหนดให้วิเคราะห์

**หากเหมาะสมรูปแบบการตอบกลับที่ต้องการ:**
-   ระบุคำถามของผู้เสนอราคา (Question)
-   ให้คำตอบที่สรุปเป็น point form (Summary Answer)
-   ระบุข้อความที่ตรงตามเงื่อนไข (Exact Sentence from pdf)
-   ระบุแหล่งที่มา (Source/Citation)

**หากเหมาะสมตัวอย่างการตอบกลับ:**
**Question:** ...
**Summary Answer:** ...
**Exact Sentence:** ...
**Source/Citation:** [ข้อ X.Y]"""
        else:  # English
            system_prompt = """You are an expert specialist in analyzing Thai government e-bidding documents.

**Your objectives are:**
1. Analyze the e-bidding purchase document provided to you (hereinafter called "Document")
2. When you receive a question from a Bidder, search for the most relevant and applicable section, clause, or text in the "Document" to answer it
3. Your answer must be the original text from the document (Direct Quote) with a clear citation of the clause number or source
4. Do not provide information that is not in the provided document

**Response format:**
- State the Bidder's question (Question)
- Provide a summarized answer in point form (Summary Answer)
- Provide the exact relevant sentence(s) from the document (Exact Sentence from Document)
- Cite the source (Source/Citation)

**Example response format:**
**Question:** ...
**Summary Answer:** ...
**Exact Sentence:** ...
**Source/Citation:** [Clause X.Y]"""
        
        messages = [{"role": "system", "content": system_prompt}]
        for msg in self.conversation_history[:-1]:  # All but the last one
            messages.append(msg)
        messages.append({"role": "user", "content": full_message})
        
        # Estimate input tokens
        input_text = "\n".join([msg["content"] for msg in messages])
        input_tokens = self._estimate_tokens(input_text)
        
        logger.info(f"Sending request with model: {self.default_model}")
        logger.info(f"Language: {language}")
        logger.info(f"Input tokens (estimated): {input_tokens}")
        logger.info(f"Messages: {messages}")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Question count: {self.question_count}/{self.max_questions}")
        
        # Stream response
        try:
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                stream=True,
                stream_options={"include_usage": True},
                # temperature=0.2,  # Low temperature for more factual responses
                # top_p=0.8  # Low top_p for more focused responses
            )
            
            full_response = ""
            chunk_count = 0
            
            for chunk in response:
                chunk_count += 1
                logger.debug(f"Received chunk {chunk_count}: {chunk}")
                
                # Check if we have choices
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        content = delta.content
                        logger.debug(f"Chunk {chunk_count} content: {content}")
                        full_response += content
                        yield content
                elif chunk.usage:
                    logger.info(f"Usage information: {chunk.usage}")
                    if hasattr(chunk.usage, 'prompt_tokens'):
                        logger.info(f"Actual prompt tokens: {chunk.usage.prompt_tokens}")
            
            logger.info(f"Completed streaming. Total chunks: {chunk_count}, Total response length: {len(full_response)}")
            logger.debug(f"Full response: {full_response}")
            
            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": full_response})
            
            # If this was the last allowed question, notify the user
            if self.question_count >= self.max_questions:
                yield "\n\n[INFO: You have used all 10 questions. The session will reset after this response.]"
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield error_msg
    
    def reset_session(self):
        """
        Reset the conversation history and knowledge base
        """
        logger.info("Resetting session")
        self.conversation_history = []
        self.knowledge_base = []
        self.question_count = 0
        self.session_id = hashlib.md5(os.urandom(32)).hexdigest()
    
    def get_question_count(self):
        """
        Get the current question count
        """
        return self.question_count
    
    def get_max_questions(self):
        """
        Get the maximum allowed questions
        """
        return self.max_questions