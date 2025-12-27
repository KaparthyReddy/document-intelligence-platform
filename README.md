# Document Intelligence Platform 📄🤖

An intelligent document analysis system that uses ML to extract insights from PDFs, images, and spreadsheets. Powered by OCR, NER, sentiment analysis, and knowledge graph generation.

## Features

- 📄 **Multi-Format Support**: PDFs, images (PNG/JPG), Excel files
- 🔍 **OCR**: Extract text from scanned documents
- 🏷️ **Named Entity Recognition**: Identify people, organizations, locations, dates
- 📊 **Document Classification**: Auto-categorize documents (invoices, contracts, reports)
- 💭 **Sentiment Analysis**: Analyze document tone and sentiment
- 🕸️ **Knowledge Graphs**: Visualize entity relationships
- ⏱️ **Timeline Extraction**: Auto-generate timelines from dates and events
- 🔎 **Semantic Search**: Search across all analyzed documents
- 📈 **Analytics Dashboard**: Real-time insights and statistics
- 💾 **Document Management**: Store, organize, and retrieve analyzed documents

## Tech Stack

**Backend:**
- FastAPI (Python async web framework)
- Transformers (Hugging Face NLP models)
- Tesseract/EasyOCR (OCR)
- spaCy (NLP and NER)
- MongoDB (document database)
- Redis (caching)

**Frontend:**
- React 18
- Recharts (charts)
- D3.js (knowledge graphs)
- Modern responsive UI

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (local or Docker)
- Redis (local or Docker)

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Start server
python app.py
```

Backend runs on `http://localhost:8000`

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

Frontend runs on `http://localhost:3000`

### Database Setup (Optional - Docker)
```bash
# Start MongoDB and Redis with Docker Compose
docker-compose up -d
```

Or install MongoDB and Redis locally:
- MongoDB: https://www.mongodb.com/try/download/community
- Redis: https://redis.io/download

## API Endpoints

- `POST /api/upload` - Upload document for analysis
- `GET /api/documents` - List all documents
- `GET /api/document/{id}` - Get document details
- `POST /api/analyze/{id}` - Analyze a document
- `GET /api/entities/{id}` - Get extracted entities
- `GET /api/sentiment/{id}` - Get sentiment analysis
- `GET /api/knowledge-graph/{id}` - Get knowledge graph
- `GET /api/search` - Search across documents

## Project Structure
```
document-intelligence-platform/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── notebooks/        # Jupyter notebooks for experiments
└── docs/            # Documentation
```

## Development Timeline

- **Day 1**: Setup, OCR, document processing
- **Day 2**: NER, sentiment analysis, classification
- **Day 3**: Frontend, knowledge graphs, integration

## Features Roadmap

- [ ] Video/audio transcription
- [ ] Multi-language support
- [ ] Collaborative annotations
- [ ] Advanced entity linking
- [ ] Document comparison
- [ ] Automated report generation

## License

MIT License
