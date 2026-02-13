import os


def get_llm(temperature=0):
    """
    Centralized LLM factory. Reads LLM_PROVIDER env var at call time
    and returns the appropriate LangChain chat model.

    Supported providers: anthropic, google, openai
    """
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower().strip()

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"),
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
            max_retries=2,
            timeout=120,
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            max_retries=2,
            timeout=120,
        )

    else:  # default: anthropic
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
            temperature=temperature,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_retries=2,
            timeout=120,
        )
