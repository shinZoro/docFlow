# DocFlow - Intelligent Document Processing System

DocFlow is an AI-powered document processing system that automatically classifies, extracts, and stores structured data from various input formats including PDFs, JSON files, and emails. Built with LangGraph and LangChain, it provides intelligent routing and data extraction capabilities.

## Features

- **Multi-format Support**: Processes PDFs, JSON data, and email content
- **Intelligent Classification**: Automatically determines input format and routes to appropriate processor
- **Structured Data Extraction**: Extracts key information like sender, recipient, amounts, dates, and more
- **Persistent Memory**: Stores processed data in SQLite database for future reference
- **Interactive Chat Interface**: Command-line chatbot for easy interaction
- **Intent Detection**: Identifies document types (Invoice, Complaint, RFQ, Regulation, etc.)

## Project Structure

```
DOCFLOW/
├── Sample Inputs/                  # Sample files for testing
│   ├── Email.txt                   # Sample email content
│   ├── Json.txt                    # Sample JSON data
│   ├── Sample Invoice.pdf          # Sample invoice document
│   └── Sample RFQ.pdf             # Sample RFQ document
├── .env                           # Environment variables
├── .gitignore                     # Git ignore file
├── .python-version               # Python version specification
├── docflow_memory.db             # SQLite database (auto-generated)
├── License.txt                   # MIT License
├── main.py                       # Main application file
├── pyproject.toml               # Project configuration
├── README.md                    # This file
└── uv.lock                      # Dependency lock file
```

## Architecture

The system uses a graph-based architecture with the following components:

```
Input → Classifier → [PDF Flow | JSON Flow | Email Flow] → Memory Storage
```

### Core Components

1. **Classifier Node**: Routes inputs based on format detection
2. **PDF Flow**: Processes PDF documents using PyPDFLoader
3. **JSON Flow**: Handles structured JSON data
4. **Email Flow**: Extracts information from email content
5. **Memory System**: SQLite database for persistent storage

## Installation

### Prerequisites

- Python 3.8+
- Required dependencies (install via pip)

### Dependencies

```bash
pip install python-dotenv
pip install langgraph
pip install langchain
pip install langchain-community
pip install pydantic
pip install pypdf
```

### Environment Setup

1. Create a `.env` file in the project root
2. Add your API credentials:

```
GROQ_API_KEY=your_groq_api_key_here
```

## Usage

### Running the Chatbot

```bash
python main.py
```

### Input Formats

#### PDF Processing

For Sample pdf and demo runs copy the path of pdf from Sample inputs folder.

```
You: /path/to/document.pdf
```

#### JSON Processing

For Sample JSON inputs go to Sample Inputs / Json.txt , while pasting in command line make sure you paste as one line.

```
You: {"invoice_id": "INV-001", "amount": 1500, "sender": "company@example.com"}
```

#### Email Processing

For Sample Email inputs go to Sample Inputs / Email.txt , while pasting in command line make sure you paste as one line.

```
You: Subject: Invoice Payment Due
From: vendor@company.com
To: accounts@mycompany.com
...
```

### Example Interactions

**PDF Document:**

```
You: ./invoices/invoice_march_2024.pdf
Assistant: Data from Pdf extracted and Saved Successfully
```

**JSON Data:**

```
You: {"type": "invoice", "total": 2500.00, "vendor": "Tech Solutions Inc"}
Assistant: Data from JSON extracted and Saved Successfully
```

**Email Content:**

```
You: From: supplier@example.com
Subject: Outstanding Invoice #12345
Due Date: 2024-03-15
Amount: $1,250.00
Assistant: Data from Email extracted and Saved Successfully
```

## Data Structure

### Extracted Data Schema

```json
{
  "source": "document_name_or_email",
  "type": "PDF|JSON|Email",
  "timestamp": "2024-01-15T10:30:00Z",
  "intent": "Invoice|Complaint|RFQ|Regulation",
  "extracted_values": {
    "sender": "sender_info",
    "recipient": "recipient_info",
    "subject": "document_subject",
    "total_amount": "monetary_value",
    "due_date": "payment_due_date",
    "issue_date": "document_date",
    "items": ["list_of_items"],
    "notes": "additional_information"
  },
  "thread_id": null
}
```

### Database Schema

The system creates a SQLite database (`docflow_memory.db`) with the following structure:

```sql
CREATE TABLE memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    type TEXT,
    timestamp TEXT,
    intent TEXT,
    extracted_values TEXT,
    thread_id TEXT
);
```

## Supported Document Types

- **Invoices**: Extracts vendor info, amounts, due dates
- **Complaints**: Identifies issues, parties involved, resolution requests
- **RFQs (Request for Quotes)**: Captures requirements, specifications, deadlines
- **Regulations**: Extracts compliance requirements, effective dates
- **General Correspondence**: Email content analysis

## Configuration

### LLM Model

The system uses Groq's Llama3-70B model by default. You can modify the model in the code:

```python
llm = init_chat_model("groq:llama3-70b-8192")
```

### Custom Prompts

Each processing flow has customizable prompts for specific extraction needs:

- `pdf_prompt`: For PDF document processing
- `json_prompt`: For JSON data validation
- `email_prompt`: For email content analysis

## Error Handling

- Invalid file paths are handled gracefully
- Malformed JSON data is processed with error flags
- Missing fields are set to null with notes in the output

## Memory and Persistence

All processed documents are automatically saved to the SQLite database with:

- Unique timestamps
- Source identification
- Extracted structured data
- Intent classification

## Gradio Web Interface (New!)

We have integrated a Gradio-powered frontend to provide an interactive web interface for DocFlow

### How it works? 

Just simply:
```bash
python main.py
```
and follow the link provided like (http://127.0.0.1:7860/)

## License

This project is licensed under the MIT License. See the [License.txt](License.txt) file for details.
