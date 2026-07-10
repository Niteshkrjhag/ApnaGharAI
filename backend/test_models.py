import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

load_dotenv()

print("Testing Model Connections...\n")

def test_model(name, llm):
    try:
        response = llm.invoke([HumanMessage(content="Reply with exactly 'OK'")])
        print(f"✅ {name} SUCCESS: {response.content.strip()}")
    except Exception as e:
        print(f"❌ {name} FAILED: {str(e)[:250]}")

# 1. OpenAI
test_model("OpenAI (gpt-4o-mini)", ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0, 
    api_key=os.getenv("OPENAI_API_KEY", "dummy"),
    max_retries=1
))

# 2. OpenRouter
test_model("OpenRouter (openrouter/free)", ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "dummy"),
    model="openrouter/free",
    temperature=0,
    max_retries=1
))

# 3. Gemini
test_model("Gemini (gemini-3.5-flash)", ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0,
    api_key=os.getenv("GEMINI_API_KEY", "dummy"),
    max_retries=1
))

# 4. Ollama Cloud
raw_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
clean_base_url = raw_base_url.rstrip("/")
if clean_base_url.endswith("/v1"):
    clean_base_url = clean_base_url[:-3]

ollama_kwargs = {
    "base_url": clean_base_url,
    "model": "gpt-oss:120b",
    "temperature": 0,
}
if os.getenv("OLLAMA_API_KEY"):
    ollama_kwargs["client_kwargs"] = {"headers": {"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"}}

test_model("Ollama Cloud", ChatOllama(**ollama_kwargs))
