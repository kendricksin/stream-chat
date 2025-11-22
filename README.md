# Streamlit Chatbot with PDF Knowledge Base

A Streamlit-based chatbot application that supports PDF uploads as a knowledge reference for question answering. The application uses DashScope API from Alibaba Cloud for generating responses through its OpenAI-compatible interface.

## Project Description

This project implements a chatbot interface that allows users to:
1. Upload PDF documents as a knowledge base
2. Ask questions about the content of those documents
3. Receive AI-generated answers based on the document content

The application uses DashScope's Qwen models via the OpenAI-compatible API to process queries and generate responses. It maintains conversation history during the session and provides a streaming interface for real-time response display.

## Vendor Requirements

To use this application, you need:

1. **DashScope API Key**:
   - Register for an account at [Aliyun DashScope](https://dashscope.console.aliyun.com/)
   - Generate an API key in the console
   - Add the key to the `.env` file

2. **Supported Models**:
   - The application is configured to use `qwen-plus` by default
   - Other supported Qwen models can be specified in the `.env` file

3. **API Endpoint**:
   - The application uses the international OpenAI-compatible API endpoint: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
   - This is automatically configured in the application

## Features

- Chat interface with streaming responses
- PDF upload and text extraction for knowledge base
- Support for DashScope APIs via OpenAI-compatible interface
- Session management that resets on page refresh
- Question limit (10 questions per session) for resource management
- Environment-based configuration
- Debug mode for troubleshooting
- Automatic PDF processing with default section selection
- Suggested questions in both Thai and English
- Section-based knowledge management for large documents
- Improved UI with clear separation between suggested questions and chat history

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   or
   ```bash
   pip install streamlit dashscope PyPDF2 python-dotenv openai
   ```

2. Set up your API keys in the `.env` file:
   ```
   DASHSCOPE_API_KEY=your_dashscope_api_key_here
   DEFAULT_MODEL=qwen-plus
   ```

## Usage

Run the application with:
```bash
streamlit run main.py
```

or

```bash
python -m streamlit run main.py
```

### How to use:

1. Upload a PDF file using the file uploader in the sidebar
2. The application will automatically process the PDF and add default sections (2, 4, 5, 6) to the knowledge base
3. Ask questions in the chat interface or click on suggested questions (in Thai or English)
4. The bot will use the PDF content as reference to answer your questions

### Session Management:

- Each session is limited to 10 questions and responses
- After reaching the limit, you'll need to upload a new PDF to start a new session
- You can manually reset the session using the "Reset Session" button

### PDF Section Management:

- After uploading a PDF, the application automatically processes it and adds default sections to the knowledge base
- You can click "Select Sections to Include" to customize which sections of the document to use as reference
- Click "Update Knowledge Base with Selected Sections" to apply your section selections

## Deployment

To deploy this application on a VM:

### Required Files:
- [main.py](file://c:\Users\Sin%20Kendrick\Desktop\stream-chat\main.py) - Main Streamlit application
- [chat_client.py](file://c:\Users\Sin%20Kendrick\Desktop\stream-chat\chat_client.py) - Chat client implementation
- [pdf_parser_v2.py](file://c:\Users\Sin%20Kendrick\Desktop\stream-chat\pdf_parser_v2.py) - PDF parsing functionality
- [requirements.txt](file://c:\Users\Sin%20Kendrick\Desktop\stream-chat\requirements.txt) - Python dependencies
- [pyproject.toml](file://c:\Users\Sin%20Kendrick\Desktop\stream-chat\pyproject.toml) - Project configuration
- [.env](file://c:\Users\Sin%20Kendrick\Desktop\stream-chat\result.json) - Environment variables (create on VM with your actual API keys)

### Deployment Steps:

1. Transfer the required files to your VM
2. Install Python 3.8+ on the VM if not already installed
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a [.env](file://c:\Users\Sin%20Kendrick\Desktop\stream-chat\result.json) file with your API keys:
   ```
   DASHSCOPE_API_KEY=your_actual_api_key_here
   DEFAULT_MODEL=qwen-plus
   ```
5. Run the application:
   ```bash
   streamlit run main.py
   ```

### Firewall/Network Configuration:

- Ensure port 8501 (default Streamlit port) is open if you want to access the application externally
- You may need to run with `streamlit run main.py --server.port 80` to use a different port
- For external access, use `streamlit run main.py --server.address 0.0.0.0`

## Debugging

If you're experiencing issues with the chat functionality, you can enable Debug Mode:

1. Check the "Debug Mode" checkbox in the sidebar
2. Expand the "Debug Information" section to see:
   - Session ID
   - Conversation history
   - Knowledge base content
3. Check the console/terminal for detailed logging information

Common issues and solutions:
- **404 Error**: Check that your model name is correct and available in your DashScope account
- **401 Error**: Verify your API key is correct and has proper permissions
- **No response**: Enable debug mode to see detailed logs of the request/response flow

## How it works

- The application maintains a conversation history during the session
- When a PDF is uploaded, its text content is extracted and stored as a knowledge base
- Each question is enhanced with the knowledge base content before being sent to the AI model
- Sessions are limited to 10 questions and responses for resource management
- Sessions are reset when the limit is reached or when the page is refreshed

## Configuration

Environment variables:
- `DASHSCOPE_API_KEY`: Your DashScope API key
- `DEFAULT_MODEL`: The default model to use (default: qwen-plus)