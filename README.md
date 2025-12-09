# Vistify: Agentic Video Intelligence System🎥✨

![Vistify Preview](./img/logo.svg)


## 🚀 Key Features

### 1. 📝 Dual-Mode Summarization
*   **10-Point Summary**: Generates a quick, digestable list of the top 10 most critical points from the video.
*   **In-Depth Summary**: Produces a comprehensive research-grade report with IEEE-style formatting, including hierarchical headings, detailed bullet points, and synthesized conclusions.

### 2. 💬 Interactive Q&A with Grounded RAG
*   **Context-Aware Chat**: Ask questions about the video content and receive answers based *exclusively* on the transcript.
*   **RAG Architecture (TF-IDF)**: Unlike generic embeddings, Vistify utilizes a **TF-IDF (Term Frequency-Inverse Document Frequency)** vectorization model. This approach ensures high precision in retrieving specific keyword-heavy transcript chunks, minimizing hallucination by grounding answers in exact textual evidence.
*   **Hallucination Prevention**: The system employs strict prompt engineering and context windowing to force the LLM to answer "I don't know" if the information is not present in the retrieved chunks.

### 3. 🧠 Deep Insights & NER (spaCy)
*   **Technical Entity Extraction**: Leverages **spaCy's Industrial-Strength NLP** models to perform Named Entity Recognition (NER) on video transcripts.
*   **Structured Data**: Automatically extracts and categorizes:
    *   **PERSON**: Key individuals mentioned.
    *   **ORG**: Companies, agencies, and institutions.
    *   **GPE/LOC**: Countries, cities, and physical locations.
    *   **DATE/TIME**: Temporal references for timeline construction.
*   **Relationship Mapping**: Custom logic analyses sentence-level co-occurrences to build a graph of relationships (e.g., "Person X is associated with Organization Y").

### 4. 📊 Real-Time Trust Metrics
Every response enables user auditing through exposed metrics:
*   **🔍 Retrieval Score**: Cosine similarity score indicating the relevance of the retrieved transcript chunks to the user's query.
*   **✅ Faithfulness**: ROUGE-1/Word Overlap score measuring how well the generated answer is supported by the context.
*   **⏱️ Latency**: Execution time for transparency.

---

## 🏗️ Technical Architecture

### Retrieval-Augmented Generation (RAG) Engine
Vistify avoids the overhead of neural embeddings for this specific use case, opting instead for a deterministic and explainable **TF-IDF** approach using `scikit-learn`:
1.  **Chunking**: Transcripts are segmented into overlapping windows to preserve context boundaries.
2.  **Vectorization**: Both the user query and transcript chunks are transformed into sparse vectors using a TF-IDF vocabulary built dynamically from the video content.
3.  **Retrieval**: We compute the **Cosine Similarity** between the query vector and all chunk vectors. The top `k` chunks are retrieved and passed to the Gemini 2.0 Flash context window.

### Named Entity Recognition (NER) Pipeline
The NER system is built on top of **spaCy** (`en_core_web_sm`) and implements a multi-stage pipeline:
1.  **Preprocessing**: Transcript text is cleaned and normalized.
2.  **Entity Recognition**: The `en_core_web_sm` model identifies entities and assigns labels (PERSON, ORG, GPE, etc.).
3.  **Entity Linking & Deduplication**: Custom heuristics merge variations of the same entity (e.g., "Barack Obama" and "Obama") to prevent duplicate reporting.
4.  **Relationship Extraction**: A rule-based engine scans for entities appearing in the same sentence structure to infer potential relationships, filtering for valid subject-object pairs.

---

## 🛠️ Tech Stack

### Backend
*   **Framework**: Python Flask (REST API)
*   **Server**: Waitress (WSGI Production Server)
*   **LLM**: **Ollama** (Model: `gpt-oss:20b`)
*   **NLP & NER**: **spaCy** (`en_core_web_sm`), `scikit-learn` (TF-IDF), `numpy`
*   **Data Acquisition**: `youtube-transcript-api`

### Frontend
*   **Core**: HTML5, CSS3 (Glassmorphism), JavaScript (ES6+)
*   **Build System**: Parcel

---

## ⚙️ Installation & Setup

### Prerequisites
*   **Node.js** (v14+)
*   **Python** (v3.8+)
*   **Ollama API Key**

### 1. Clone & Install
```bash
git clone https://github.com/justishika/Vistify-video-intelligence.git
cd Video-Gist-Generator
```

### 2. Backend Setup
```bash
cd Flask-API
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install spacy

# Download required spaCy NLP model
python -m spacy download en_core_web_sm
```

**Configuration**:
Update `Flask-API/config.py` with your API key:
```python
OLLAMA_API_KEY = 'YOUR_ACTUAL_API_KEY_HERE'
```

**Start Server**:
```bash
python start_server.py
```

### 3. Frontend Setup
```bash
cd ..  # Return to root
npm install
npm start
```
Access the app at `http://localhost:1234`.

---

> Done in collaboration with [Hariprasad-791](https://github.com/Hariprasad-791)

## 📄 License
MIT License
