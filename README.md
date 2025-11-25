# Chatbot Bình Dân Học Vụ Số (BDHVS)

AI-powered chatbot for exam regulations and student support using RAG (Retrieval-Augmented Generation).

## 🏗️ Project Structure

```
chatbot-bdhvs/
├── frontend/          # Next.js 15 App Router
│   ├── app/           # App Router pages
│   ├── components/    # React components
│   ├── lib/           # Utility libraries
│   └── public/        # Static assets
├── backend/           # Python FastAPI
│   ├── app/           # Clean Architecture
│   │   ├── api/       # API endpoints
│   │   ├── core/      # Configuration
│   │   ├── schemas/   # Pydantic models
│   │   └── services/  # Business logic (RAG)
│   ├── data/          # PDFs & Vector DB
│   └── tests/         # Unit tests
├── docker-compose.yml # Container orchestration
└── README.md
```

## 🚀 Tech Stack

### Frontend
- **Framework:** Next.js 15.5 (App Router)
- **React:** 19
- **Styling:** Tailwind CSS + Shadcn UI
- **Theme:** Dark/Light mode with next-themes

### Backend
- **Framework:** FastAPI 0.115
- **LLM:** Llama 3.3 70B (via MegaLLM)
- **Embeddings:** FastEmbed (BAAI/bge-small-en-v1.5)
- **Vector Store:** FAISS
- **RAG:** LangChain LCEL

## 🛠️ Development Setup

### Backend
\`\`\`bash
cd backend
pip install -r requirements.txt
echo "MEGALLM_API_KEY=your_key" > .env
python -m app.main
\`\`\`

### Frontend
\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

### Docker
\`\`\`bash
echo "MEGALLM_API_KEY=your_key" > .env
docker-compose up --build
\`\`\`

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/chat` | Chat with RAG |
| POST | `/api/v1/search` | Similarity search |

## 📄 License

MIT License
