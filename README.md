# ApnaGharAI

> **Smart Estimation for Tomorrow's Construction.**

ApnaGharAI is a reality-aware estimation engine for rural and semi-urban home construction. Unlike standard calculators that simply multiply square footage by a base rate, ApnaGharAI utilizes a true Multi-Agent system to scrape live market data, calculate local friction (monopolies, logistics, weather delays), and provide a mathematically certain financial blueprint.

## 🏗️ Architecture: The "Split Engine"

To prevent AI mathematical hallucinations, the architecture strictly separates reasoning from math. Here is how the system works behind the scenes:

```mermaid
flowchart TD
    classDef user fill:#2a85ff,color:#fff,stroke:#fff,stroke-width:2px;
    classDef agent fill:#f5a623,color:#fff,stroke:#fff,stroke-width:2px;
    classDef math fill:#4caf50,color:#fff,stroke:#fff,stroke-width:2px;
    classDef result fill:#9c27b0,color:#fff,stroke:#fff,stroke-width:2px;

    User("👤 You Provide Your Village Details"):::user
    
    subgraph AI Agents (The Researchers)
        direction TB
        Macro("🌍 Global Expert\nChecks global steel & oil trends"):::agent
        Regional("🚚 State Expert\nChecks transport & labor costs"):::agent
        Micro("🏡 Village Expert\nChecks local monopolies & harvest risks"):::agent
    end

    Judge("⚖️ The Judge Agent\nReviews all facts & stops AI hallucinations"):::agent
    Calculator("🧮 The Math Engine\nCalculates the exact budget (No AI Math Allowed)"):::math
    Output("📄 Your Final Blueprint & Explanation"):::result

    User --> Macro
    User --> Regional
    User --> Micro
    
    Macro --> Judge
    Regional --> Judge
    Micro --> Judge
    
    Judge -->|"Approved Costs"| Calculator
    Calculator --> Output
```

1. **The Observers (AI Agents):** Three parallel agents (Macro, Regional, Micro) use DuckDuckGo to scrape live web data regarding geopolitical commodity shocks, state-level logistics, and village-level harvest cycles.
2. **The Safety Net (Python Clamps):** AI proposals are piped through strict, dynamic Python constraints to prevent wild hallucinated numbers from destroying the budget.
3. **The Synthesizer (Judge Agent):** Synthesizes the data, applies circuit breakers (e.g., DIY labor nullifies weather delay costs), and generates a plain-English transcript.
4. **The Calculator (Deterministic Math Engine):** A strict Python FastAPI/Pydantic engine that computes the final cost and monthly savings goals with absolute mathematical certainty.

## 🚀 Tech Stack
- **Frontend:** React (Vite), JavaScript, Vanilla CSS (Glassmorphism architecture)
- **Backend:** Python, FastAPI, Uvicorn, Pydantic
- **AI/Agents:** LangChain (Tools), `meta-llama/llama-3.1-8b-instruct:free` (OpenRouter), `gpt-oss:120b` (Ollama), `asyncio` for parallel orchestration.

---

## 💻 How to Run Locally

You will need to open **two separate terminal windows** to run the backend server and the frontend interface simultaneously.

### 1. Start the FastAPI Backend
```bash
cd backend
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
uvicorn main:app --reload --port 8000
```
*The backend will run on `http://localhost:8000`*

### 2. Start the React Frontend
```bash
cd frontend
npm install  # If running for the first time
npm run dev
```
*The frontend will run on `http://localhost:5173`*

---

## 🔑 Environment Variables
In the `/backend` directory, create a `.env` file (you can copy `.env.example`) and configure your LLM keys:
```env
OPENROUTER_API_KEY="your_openrouter_key"
# Optional Local LLM Fallback
OLLAMA_BASE_URL="http://localhost:11434"
```
