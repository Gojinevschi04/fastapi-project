"""OpenAI Realtime token pricing (USD per 1M tokens).

Source: OpenAI pricing page for gpt-4o-realtime-preview as of 2026-Q1.
Kept in sync with the FE copy in `src/types/call.ts`.
"""

OPENAI_REALTIME_PRICE_PER_MILLION_USD = {
    "input_audio": 32.0,
    "output_audio": 64.0,
    "input_text": 4.0,
    "output_text": 16.0,
}

TOKENS_PER_MILLION = 1_000_000
COST_DECIMAL_PLACES = 4


def estimate_cost_usd(
    input_audio_tokens: int,
    output_audio_tokens: int,
    input_text_tokens: int,
    output_text_tokens: int,
) -> float:
    """Compute the estimated USD cost for a token breakdown."""
    rates = OPENAI_REALTIME_PRICE_PER_MILLION_USD
    total = (
        input_audio_tokens * rates["input_audio"]
        + output_audio_tokens * rates["output_audio"]
        + input_text_tokens * rates["input_text"]
        + output_text_tokens * rates["output_text"]
    ) / TOKENS_PER_MILLION
    return round(total, COST_DECIMAL_PLACES)
