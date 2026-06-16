# Cenz-AI  (An AI-Driven Multi-Modal Platform for Automated Detection, Analysis, and Redaction of Personally Identifiable Information Across Text, Images, Audio, and Video Content)

Cenz-AI is a web-based platform for detecting and redacting Personally Identifiable Information (PII) from different types of content. The project was built to explore how AI can be used to improve privacy compliance by automatically identifying sensitive information across text, images, audio, and video files.
Instead of manually reviewing files and removing confidential information, users can upload content and allow the system to detect and mask sensitive data automatically.

## Motivation
Organizations frequently work with documents, recordings, and media files that contain personal information such as names, email addresses, phone numbers, addresses, and identification numbers.
Manual redaction is often slow, inconsistent, and difficult to scale. The purpose of this project is to provide a centralized solution that can process multiple content formats while reducing the effort required to protect sensitive data.

## Features

### Text Processing
- Detects sensitive information in plain text
- Identifies common PII entities
- Generates redacted output

### Document and OCR Support
- Extracts text from scanned documents and images
- Performs OCR-based analysis
- Detects and masks confidential information

### Audio Processing
- Converts speech into text
- Identifies sensitive information within transcripts
- Supports privacy-focused audio analysis

### Video Processing
- Analyzes video content
- Detects visible text and sensitive information
- Supports automated redaction workflows

### AI-Based Detection
- Entity recognition for personal information
- Automated masking and replacement
- Multi-format content processing

## Technology Stack

### Frontend
- Next.js
- JavaScript
- Tailwind CSS

### Backend
- Python
- FastAPI
- REST APIs

### Processing Components
- OCR Engine
- Natural Language Processing
- Speech-to-Text Models
- Computer Vision Techniques

---

## Project Structure

```text
Cenz-AI/
│
├── frontend/
│   ├── app/
│   ├── public/
│   ├── package.json
│   └── next.config.mjs
│
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── runtime.txt
│
└── README.md
## Installation
### Clone the Repository
```bash
git clone https://github.com/bandhav100/Cenz-AI.git
cd Cenz-AI
```
### Backend Setup

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

The application will be available locally after both services are running.

---

## Workflow

1. Upload a file or input content.
2. The system determines the content type.
3. Appropriate processing modules are executed.
4. Sensitive information is detected.
5. Redaction rules are applied.
6. A sanitized version of the content is generated.
7. 
## Use Cases

- Privacy compliance
- Legal document review
- Healthcare records
- Customer support recordings
- Research datasets
- Internal enterprise documentation

## Future Improvements

- Support for additional languages
- Custom redaction policies
- Batch processing
- Audit logs
- User authentication and access control
- Real-time redaction services

---
## Deployment

Frontend and backend services are deployed using cloud hosting platforms to provide public access and testing.

## Author
Bandhav
https://github.com/bandhav100
Built as part of an effort to explore practical applications of AI in privacy protection and compliance automation.
