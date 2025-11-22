# Streamlit Chatbot with PDF Knowledge Base

A Streamlit-based chatbot application that supports PDF uploads as a knowledge reference for question answering. The application supports multiple AI providers through OpenAI-compatible APIs, including Google Gemini and Alibaba DashScope.

## Project Description

This project implements a chatbot interface that allows users to:
1. Upload PDF documents as a knowledge base
2. Ask questions in Thai or English about the document content
3. Receive AI-generated answers based on the document content
4. Switch between different AI providers (DashScope, Gemini, etc.)

The application maintains conversation history during the session and provides a streaming interface for real-time response display.

## Supported Providers

The application is provider-agnostic and supports any OpenAI-compatible API:

### 1. **Google Gemini** (Recommended)
- Models: `gemini-1.5-pro`, `gemini-2.0-flash`, `gemini-2.0-flash-lite`
- Endpoint: `https://generativelanguage.googleapis.com/v1beta/openai/`
- [Get API Key](https://aistudio.google.com/apikey)

### 2. **DashScope (Alibaba Cloud)**
- Models: `qwen-turbo`, `qwen-plus`, `qwen-max`, `qwen3-max`
- Endpoint: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- [Get API Key](https://dashscope.console.aliyun.com/)

## Features

- 🎯 **Bilingual Support**: Thai and English system prompts and suggested questions
- 📱 **Compact UI**: Optimized styling for better space utilization
- 📊 **PDF Processing**: Automatic text extraction with section-based knowledge management
- 🔄 **Streaming Responses**: Real-time response display
- 💾 **Session Management**: 10-question per session limit with auto-reset
- 🔐 **Secure Secrets**: Uses Streamlit's `secrets.toml` for API credentials
- 🌐 **Multi-Provider**: Works with any OpenAI-compatible API
- 🎭 **Language Selection**: Automatically selects appropriate system prompt based on user's question language

## Setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd stream-chat
uv sync
```

Or with pip:
```bash
pip install -r requirements.txt
```

### 2. Configure API Credentials

Create `.streamlit/secrets.toml` in your project root:

```toml
# For Google Gemini
API_KEY = "your_gemini_api_key_here"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_MODEL = "gemini-1.5-pro"

# For DashScope
# API_KEY = "your_dashscope_api_key_here"
# BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
# DEFAULT_MODEL = "qwen3-max"
```

See `.streamlit/secrets.toml.example` for a template.

## Usage

Run the application with:
```bash
streamlit run src/main.py
```

Or with uv:
```bash
uv run streamlit run src/main.py
```

### How to Use

1. **Upload a PDF**: Use the "Upload PDF" section in the left sidebar
2. **Automatic Processing**: The app automatically extracts text and adds default sections to the knowledge base
3. **Ask Questions**:
   - Click suggested questions (Thai or English) for pre-formatted queries
   - Or type your own questions in the chat input box
4. **Language Selection**: The system automatically detects your question language and uses the appropriate system prompt
5. **Reset Session**: Use the "Reset Session" button at the top of the sidebar to start fresh

### Session Management

- Each session is limited to **10 questions**
- A new session starts when you upload a new PDF
- Click "Reset Session" to manually reset and clear conversation history
- The session automatically resets when the 10-question limit is reached

### PDF Section Management

After uploading a PDF, you can:
- Automatically use default sections (2, 4, 5, 6)
- Click "Select Sections to Include" to customize which sections to use
- Click "Update Knowledge Base with Selected Sections" to apply changes

## Deployment

### On Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" and connect your GitHub repository
4. In app settings, add your secrets:
   ```
   [secrets]
   API_KEY = "your_api_key_here"
   BASE_URL = "https://your_api_endpoint/"
   DEFAULT_MODEL = "your_model_name"
   ```

### On a VM/Self-Hosted

#### Required Files:
- `src/main.py` - Main Streamlit application
- `src/chat_client.py` - Chat client implementation
- `src/pdf_parser_v2.py` - PDF parsing functionality
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project configuration
- `.streamlit/secrets.toml` - API configuration (create on VM)

#### Deployment Steps:

1. Install Python 3.10+ on the VM
2. Clone or transfer the project files
3. Install dependencies:
   ```bash
   uv sync
   ```
   or
   ```bash
   pip install -r requirements.txt
   ```
4. Create `.streamlit/secrets.toml` with your API credentials:
   ```toml
   API_KEY = "your_actual_api_key_here"
   BASE_URL = "https://your_api_endpoint/"
   DEFAULT_MODEL = "your_model_name"
   ```
5. Run the application:
   ```bash
   streamlit run src/main.py
   ```

#### Firewall/Network Configuration:

- Default port: **8501** (open in firewall if accessing externally)
- Custom port: `streamlit run src/main.py --server.port 80`
- External access: `streamlit run src/main.py --server.address 0.0.0.0`
- Production: Consider using a reverse proxy (Nginx, Apache) in front of Streamlit

## Troubleshooting

### API Errors

| Error | Solution |
|-------|----------|
| **404 Not Found** | Check that your model name is available with your provider |
| **401 Unauthorized** | Verify your API key is correct in `secrets.toml` |
| **Chat input disappears** | Refresh the page or check browser console for errors |
| **Slow responses** | Check API provider status and internet connection |

### Check Logs

Run with verbose logging:
```bash
streamlit run src/main.py --logger.level=debug
```

## How it works

- The application maintains a conversation history during the session
- When a PDF is uploaded, its text content is extracted and stored as a knowledge base
- Each question is enhanced with the knowledge base content before being sent to the AI model
- Sessions are limited to 10 questions and responses for resource management
- Sessions are reset when the limit is reached or when the page is refreshed

## Configuration

Secrets (in `.streamlit/secrets.toml`):
- `API_KEY`: Your API key for the selected provider (required)
- `BASE_URL`: The API endpoint URL (required)
- `DEFAULT_MODEL`: The model to use (required)

## Architecture

### File Structure

```
stream-chat/
├── src/
│   ├── main.py              # Main Streamlit application
│   ├── chat_client.py       # OpenAI-compatible chat client
│   └── pdf_parser_v2.py     # PDF text extraction and parsing
├── .streamlit/
│   ├── secrets.toml         # API credentials (git-ignored)
│   └── secrets.toml.example # Template for secrets
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project metadata
└── README.md               # This file
```

### Key Components

1. **ChatClient**: Manages API interactions and conversation state
   - Supports any OpenAI-compatible API
   - Language-specific system prompts (Thai/English)
   - Streaming response support
   - Session and token management

2. **Main App**: Streamlit UI
   - Compact, responsive design
   - Sidebar controls (Reset, PDF upload, Section management)
   - Suggested questions in Thai/English
   - Real-time chat interface

3. **PDF Parser**: Document processing
   - Section-based extraction
   - Multi-language support

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.