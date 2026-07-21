# FinSight Agent: Autonomous Financial Research

Module 2 of FinSight AI, a personal financial intelligence platform I built to support my own investment research.

This tool lets you ask plain-English questions about any company and get a comprehensive research report synthesized from multiple live data sources — current stock data, recent news, SEC filings, and web search. Rather than querying one source at a time, the agent autonomously decides which tools to use and combines the results into a single coherent answer.

---

## What it does

- Accepts any company research question in plain English
- Autonomously decides which combination of tools to use based on the question
- Pulls current stock price and company overview from Yahoo Finance
- Fetches recent news articles from NewsAPI
- Searches previously uploaded SEC filings from FinSight RAG (Module 1)
- Falls back to web search via Tavily when filings are unavailable or additional context is needed
- Maintains conversation history so follow-up questions work naturally
- Built on a client-server architecture — FastAPI backend, Streamlit frontend

---

## Architecture

```
User submits a question via Streamlit (port 8501)
    |
    v
Streamlit sends POST request to FastAPI (port 8000)
    |
    v
FastAPI passes question + conversation history to run_agent()
    |
    v
Agent sends messages + tool definitions to Claude (claude-sonnet-5)
    |
    v
Claude decides which tools to call and in what order
    |
    v
Agent dispatcher runs the requested tools:

    get_stock_price()     -> yfinance (live stock data)
    get_news()            -> NewsAPI (recent headlines)
    search_sec_filing()   -> ChromaDB (uploaded 10-K from Module 1)
    search_web()          -> Tavily (web search for gaps)

    |
    v
Tool results added to conversation and sent back to Claude
    |
    v
Claude synthesizes all results into a research report
    |
    v
FastAPI returns the report to Streamlit
    |
    v
Report displayed in the chat interface
```

### Key architectural decisions

**Agentic tool-calling loop**
Rather than hardcoding which tools to call, Claude autonomously decides based on the question. A question about recent news triggers get_news. A question about financials triggers search_sec_filing. A broad research request triggers all four tools in sequence. The loop runs until Claude has enough information to write a complete answer or hits the 10-iteration safety limit.

**Conversation history**
The full chat history is passed to the agent on every request. This gives Claude context for follow-up questions so the user can ask "tell me more about that" or "how does that compare to last year" without repeating themselves.

**Four-tool hierarchy**
Tools are ordered by data quality. Stock data and news provide real-time context. SEC filings provide deep financial detail. Web search fills gaps when filings are unavailable or the question requires broader context. Claude uses this hierarchy implicitly based on the tool descriptions.

**Client-server separation**
The agent logic lives in a FastAPI backend completely separate from the Streamlit frontend. This means the same agent can be called from a scheduled daily report, a different frontend, or any other client without changing the core logic.

**Fuzzy company name matching**
The filing registry uses rapidfuzz to match company names so users can type "Apple" or "AAPL" or "Apple Inc" and get the right filing. Exact string matching would break on minor variations.

**Provider-agnostic design**
The LLM layer is isolated to a single configuration line. Switching from Anthropic to AWS Bedrock or Azure OpenAI requires changing one string, with no changes to tool logic or the agent loop.

---

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Anthropic Claude (claude-sonnet-5) |
| Agent framework | Anthropic tool-calling API (built from scratch) |
| Stock data | yfinance (Yahoo Finance) |
| News | NewsAPI |
| SEC filings | ChromaDB via FinSight RAG (Module 1) |
| Web search | Tavily |
| Fuzzy matching | rapidfuzz |
| Backend | FastAPI + uvicorn |
| Frontend | Streamlit |
| Language | Python 3.12 |

---

## Setup

**Requirements:** Python 3.12, an Anthropic API key, a NewsAPI key, and a Tavily API key.

- Anthropic: [console.anthropic.com](https://console.anthropic.com)
- NewsAPI: [newsapi.org](https://newsapi.org)
- Tavily: [tavily.com](https://tavily.com)

```bash
# Clone the repo
git clone https://github.com/PPatel98/finsight-agent.git
cd finsight-agent

# Create and activate a virtual environment
python3.12 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Set your API keys
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.zprofile
echo 'export NEWS_API_KEY="your-key-here"' >> ~/.zprofile
echo 'export TAVILY_API_KEY="your-key-here"' >> ~/.zprofile
source ~/.zprofile

# Terminal 1 — start the FastAPI backend
uvicorn api:app --reload --port 8000

# Terminal 2 — start the Streamlit frontend
streamlit run app.py
```

The app opens at `http://localhost:8501`.

For SEC filing search to work, upload a 10-K first using [FinSight RAG](https://github.com/PPatel98/finsight-rag) (Module 1). The filing registry is shared between both modules automatically.

---

## Example questions

```
Research Apple for me
What is Nvidia's current stock price and recent news?
What does Apple's 2025 10-K say about their AI strategy?
Compare Apple's risk factors to their revenue growth
What happened to Meta's stock this week?
Give me a full investment overview of Duke Energy
```

Follow-up questions work naturally:
```
You:   Research Apple for me
Agent: [full report]
You:   Tell me more about their risk factors
Agent: [expands on risk factors with document context]
You:   How does that compare to their cash position?
Agent: [compares using filing data]
```

---

## Project structure

```
finsight-agent/
    tools.py        Four tool functions and their Claude definitions
    agent.py        Agentic loop — sends messages, handles tool calls, returns answer
    api.py          FastAPI backend — exposes the agent as a REST endpoint
    app.py          Streamlit frontend — chat interface and session management
    requirements.txt
    README.md
```

---

## Part of FinSight AI

This is Module 2 of a larger platform I am building for personal investment research.

| Module | Repo | Description | Status |
|---|---|---|---|
| 1 - Document Intelligence | [finsight-rag](https://github.com/PPatel98/finsight-rag) | Ask questions about any financial PDF | Complete |
| 2 - Research Agent | [finsight-agent](https://github.com/PPatel98/finsight-agent) | Autonomous multi-source company research | Complete |

---

## Author

Parth Patel, Software Engineer

- LinkedIn: [linkedin.com/in/parth-p75](https://linkedin.com/in/parth-p75)
- GitHub: [github.com/PPatel98](https://github.com/PPatel98)
