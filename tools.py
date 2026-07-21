import yfinance as yf
import requests
import os
from rapidfuzz import process, fuzz


def get_stock_price(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        "ticker": ticker,
        "company_name": info.get("longName", "N/A"),
        "current_price": info.get("currentPrice", "N/A"),
        "change_percent": info.get("52WeekChange", "N/A"),
        "market_cap": info.get("marketCap", "N/A"),
        "sector": info.get("sector", "N/A"),
        "summary": info.get("longBusinessSummary", "N/A")
    }


def get_news(company_name: str) -> list:
    api_key = os.getenv("NEWS_API_KEY")

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": company_name,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": api_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    articles = []
    for article in data.get("articles", []):
        articles.append({
            "title": article.get("title", "N/A"),
            "description": article.get("description", "N/A"),
            "published": article.get("publishedAt", "N/A"),
            "source": article.get("source", {}).get("name", "N/A")
        })

    return articles


def search_sec_filing(company_name: str, query: str, year: str = None) -> str:
    import chromadb
    import json
    from chromadb.utils import embedding_functions

    # Load the filing registry
    registry_path = "../finsight-rag/filing_registry.json"

    if not os.path.exists(registry_path):
        return "No filings found. Please upload a 10-K in FinSight RAG first."

    with open(registry_path, "r") as f:
        registry = json.load(f)

    if not registry:
        return "No filings found. Please upload a 10-K in FinSight RAG first."

    # Fuzzy match the company name against registry keys
    company_names = list(registry.keys())
    match = process.extractOne(
        company_name,
        company_names,
        scorer=fuzz.WRatio,
        score_cutoff=60
    )

    if not match:
        return f"No filing found for '{company_name}'. Available companies: {', '.join(company_names)}"

    matched_company = match[0]
    company_filings = registry[matched_company]

    # If year specified use it, otherwise use most recent year
    if year and year in company_filings:
        collection_id = company_filings[year]
    else:
        latest_year = max(company_filings.keys())
        collection_id = company_filings[latest_year]
        year = latest_year

    print(f"Searching {matched_company} {year} filing: {collection_id}")

    # Search ChromaDB
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    chroma_client = chromadb.PersistentClient(
        path="../finsight-rag/chroma_db"
    )

    try:
        collection = chroma_client.get_collection(
            name=collection_id,
            embedding_function=embedding_fn
        )

        results = collection.query(
            query_texts=[query],
            n_results=5
        )

        chunks = results["documents"][0]
        header = f"Source: {matched_company} {year} 10-K filing\n\n"
        return header + "\n\n---\n\n".join(chunks)

    except Exception as e:
        return f"Error searching filing for {matched_company}: {str(e)}"

def search_web(query: str) -> list:
    from tavily import TavilyClient
    
    api_key = os.getenv("TAVILY_API_KEY")
    client = TavilyClient(api_key=api_key)
    
    response = client.search(
        query=query,
        max_results=5,
        search_depth="advanced"
    )
    
    results = []
    for result in response.get("results", []):
        results.append({
            "title": result.get("title", "N/A"),
            "content": result.get("content", "N/A"),
            "url": result.get("url", "N/A")
        })
    
    return results

tools = [
    {
        "name": "get_stock_price",
        "description": "Get the current stock price, market cap, sector, and business summary for a company. Use this when the user asks about a stock price, company valuation, or wants a general company overview.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol. For example AAPL for Apple, NVDA for Nvidia, DUK for Duke Energy."
                }
            },
            "required": ["ticker"]
        }
    },
    {
        "name": "get_news",
        "description": "Get the 10 most recent news articles about a company. Use this when the user wants to know about recent developments, news, or events related to a company.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "The full company name to search news for. For example Apple Inc, Nvidia Corporation, Duke Energy."
                }
            },
            "required": ["company_name"]
        }
    },
    {
        "name": "search_sec_filing",
        "description": "Search a previously uploaded SEC filing or 10-K for relevant information about a company. Use this when the user asks about financials, risk factors, business segments, revenue, or anything that would be in an annual report. You can optionally specify a year — if not specified, the most recent filing is used.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "The company name to search filings for. For example Apple, Nvidia, Meta. Fuzzy matching is used so exact name is not required."
                },
                "query": {
                    "type": "string",
                    "description": "What to search for in the filing. For example revenue growth, risk factors, AI strategy, business segments."
                },
                "year": {
                    "type": "string",
                    "description": "Optional. The fiscal year of the filing to search, for example 2025 or 2024. If not provided, the most recent filing is used."
                }
            },
            "required": ["company_name", "query"]
        }
    },
    {
        "name": "search_web",
        "description": "Search the web for current information about a company, market conditions, or financial topics. Use this when the user asks about recent events, information not in the SEC filing, or when no filing is available for the requested year. Also use this to supplement other tools with current context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific — for example 'Apple Inc 2026 annual revenue' or 'Apple AI strategy 2026' rather than just 'Apple'."
                }
            },
            "required": ["query"]
        }
    }
]