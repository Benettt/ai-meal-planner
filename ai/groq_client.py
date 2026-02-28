from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

_client: Groq | None = None


def get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing. Add it to your .env file.")
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def stream_response(system_prompt: str, user_prompt: str, placeholder=None) -> str:
    """
    Stream Groq response token by token.
    If a Streamlit placeholder is passed, updates it live.
    """
    client = get_client()
    full_text = ""

    with client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        max_tokens=4096,
        temperature=0.7,
        stream=True,
    ) as stream:
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full_text += delta
            if placeholder:
                placeholder.markdown(full_text + "▌")

    if placeholder:
        placeholder.markdown(full_text)
    return full_text


def single_response(system_prompt: str, user_prompt: str) -> str:
    """Non-streaming call — returns complete response text."""
    client = get_client()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        max_tokens=4096,
        temperature=0.7,
    )
    return resp.choices[0].message.content