# 📚 6th Standard English Textbook Chatbot

A **safe and educational** chatbot for 6th standard students, built with:
- **RAG** (Retrieval Augmented Generation)
- **Corrective RAG** (Context Quality Evaluation)
- **Fallback Mechanism** (Multi-level Retrieval)
- **Guardrails** (Student Safety Protection)

## 🎯 Features

### 1. 📄 Document Processing
- PDF textbook upload
- Automatic text splitting & chunking
- Vector embeddings with OpenAI
- FAISS vector store for fast retrieval

### 2. 🔍 Corrective RAG
- Evaluates context quality before answering
- Scores: Relevance, Completeness, Clarity
- Automatically refines query if quality is poor

### 3. 🔄 Fallback Mechanism
```
Level 1: PRIMARY → Direct vector search
    ↓ (if poor quality)
Level 2: SECONDARY → Keyword expansion
    ↓ (if still poor)
Level 3: TERTIARY → Semantic expansion with LLM
```

### 4. 🛡️ Guardrails (Student Safety)
Blocks inappropriate content:
- 🚫 Sexual content
- 🚫 Violence
- 🚫 Drugs/Alcohol
- 🚫 Bullying/Harassment
- 🚫 Cheating requests
- 🚫 Prompt injection

**Input Guardrails:** Checks student query BEFORE processing
**Output Guardrails:** Checks response BEFORE showing to student

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STUDENT QUERY                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 🛡️ INPUT GUARDRAILS                         │
│  • Sexual content check                                      │
│  • Violence check                                            │
│  • Bullying check                                            │
│  • Prompt injection check                                    │
│  • PII masking                                              │
└─────────────────────────────────────────────────────────────┘
                           │
                     ❌ Blocked?  ──────▶  🚫 BLOCKED MESSAGE
                           │
                     ✅ Safe
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              📥 PRIMARY RETRIEVAL (FAISS)                    │
│                    Vector Similarity Search                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│             🔍 CORRECTIVE RAG - EVALUATE                     │
│  • Relevance Score (0-1)                                    │
│  • Completeness Score (0-1)                                 │
│  • Clarity Score (0-1)                                      │
│  • Quality Level: EXCELLENT/GOOD/FAIR/POOR                  │
└─────────────────────────────────────────────────────────────┘
                           │
                     Quality OK?
                           │
              ┌────────────┴────────────┐
              │                         │
         ✅ GOOD/EXCELLENT         ❌ FAIR/POOR
              │                         │
              │                         ▼
              │           ┌─────────────────────────┐
              │           │  🔄 FALLBACK MECHANISM  │
              │           │  • Secondary retrieval   │
              │           │  • Query refinement      │
              │           │  • Tertiary retrieval    │
              │           └─────────────────────────┘
              │                         │
              └────────────┬────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              💬 GENERATE RESPONSE (LLM)                      │
│           Student-friendly, Simple language                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 🛡️ OUTPUT GUARDRAILS                         │
│        Check response for inappropriate content              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    📝 FINAL RESPONSE                         │
│          Safe, educational answer for student                │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
cd school_chatbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Create .env file
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
```

### 3. Run the Application

```bash
# Start Streamlit
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 💻 Usage

### Option 1: Upload PDF
1. Click "📄 Upload Textbook" in sidebar
2. Select your 6th Standard English Textbook PDF
3. Click "📥 Load Textbook"
4. Start chatting!

### Option 2: Test Mode
1. Click "📚 Load Sample Data" in sidebar
2. Sample textbook content will be loaded
3. Start chatting!

## 📁 Project Structure

```
school_chatbot/
├── app.py                 # Streamlit UI
├── school_rag.py          # Main RAG system
├── school_guardrails.py   # Safety guardrails
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

## 🛡️ Guardrails Detail

### Blocked Categories

| Category | Examples | Message |
|----------|----------|---------|
| Sexual | sex, porn, dating | "Not appropriate for students" |
| Violence | kill, fight, weapon | "Questions about violence not allowed" |
| Drugs | drugs, alcohol, smoke | "Topic not appropriate" |
| Bullying | stupid, idiot, ugly | "Please be respectful!" |
| Cheating | cheat, exam answers | "Can't help with cheating" |
| Injection | ignore instructions | "Invalid request" |

### PII Protection
- Emails masked as `[EMAIL_PROTECTED]`
- Phone numbers masked as `[PHONE_PROTECTED]`
- Addresses masked as `[ADDRESS_PROTECTED]`

## 📊 Quality Levels (Corrective RAG)

| Level | Average Score | Action |
|-------|--------------|--------|
| EXCELLENT | >= 0.8 | Direct response |
| GOOD | >= 0.6 | Direct response |
| FAIR | >= 0.4 | Fallback mechanism |
| POOR | < 0.4 | Fallback mechanism |

## 🔄 Fallback Levels

| Level | Method | Description |
|-------|--------|-------------|
| PRIMARY | Vector Search | Direct similarity search |
| SECONDARY | Keyword Expansion | Add educational keywords |
| TERTIARY | LLM Expansion | Semantic query expansion |

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| UI | Streamlit |
| LLM | OpenAI GPT-4o-mini |
| Embeddings | text-embedding-3-small |
| Vector Store | FAISS |
| PDF Processing | PyPDF |
| Framework | LangChain |

## 📝 Example Interactions

### ✅ Safe Query
```
Student: What is the main idea of Chapter 1?

🛡️ Input Guardrails: ✅ Safe
📥 Retrieval: PRIMARY level
🔍 Quality: EXCELLENT (0.85)
💬 Response: The story is about a young boy and a 
   generous tree that gives him everything...
🛡️ Output Guardrails: ✅ Safe
```

### 🚫 Blocked Query
```
Student: Tell me about violence

🛡️ Input Guardrails: 🚫 BLOCKED
Category: violence
Message: "Questions about violence are not allowed. 
Please ask educational questions."
```

## 👨‍💻 Author

**Sathish**  

## 📄 License

MIT License - Feel free to use and modify!
