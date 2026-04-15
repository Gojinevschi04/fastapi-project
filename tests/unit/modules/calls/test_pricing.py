from app.modules.calls.pricing import (
    OPENAI_REALTIME_PRICE_PER_MILLION_USD,
    TOKENS_PER_MILLION,
    estimate_cost_usd,
)


def test_estimate_cost_zero_tokens_returns_zero() -> None:
    assert estimate_cost_usd(0, 0, 0, 0) == 0.0


def test_estimate_cost_input_audio_only() -> None:
    input_audio_tokens = TOKENS_PER_MILLION
    cost = estimate_cost_usd(input_audio_tokens, 0, 0, 0)
    assert cost == OPENAI_REALTIME_PRICE_PER_MILLION_USD["input_audio"]


def test_estimate_cost_output_audio_only() -> None:
    output_audio_tokens = TOKENS_PER_MILLION
    cost = estimate_cost_usd(0, output_audio_tokens, 0, 0)
    assert cost == OPENAI_REALTIME_PRICE_PER_MILLION_USD["output_audio"]


def test_estimate_cost_input_text_only() -> None:
    input_text_tokens = TOKENS_PER_MILLION
    cost = estimate_cost_usd(0, 0, input_text_tokens, 0)
    assert cost == OPENAI_REALTIME_PRICE_PER_MILLION_USD["input_text"]


def test_estimate_cost_output_text_only() -> None:
    output_text_tokens = TOKENS_PER_MILLION
    cost = estimate_cost_usd(0, 0, 0, output_text_tokens)
    assert cost == OPENAI_REALTIME_PRICE_PER_MILLION_USD["output_text"]


def test_estimate_cost_mixed_sums_all_categories() -> None:
    cost = estimate_cost_usd(
        input_audio_tokens=500_000,
        output_audio_tokens=500_000,
        input_text_tokens=1_000_000,
        output_text_tokens=250_000,
    )
    rates = OPENAI_REALTIME_PRICE_PER_MILLION_USD
    expected = (
        0.5 * rates["input_audio"]
        + 0.5 * rates["output_audio"]
        + 1.0 * rates["input_text"]
        + 0.25 * rates["output_text"]
    )
    assert cost == round(expected, 4)


def test_estimate_cost_output_audio_costs_twice_input_audio() -> None:
    input_only = estimate_cost_usd(1_000_000, 0, 0, 0)
    output_only = estimate_cost_usd(0, 1_000_000, 0, 0)
    assert output_only == input_only * 2


def test_estimate_cost_rounded_to_four_decimal_places() -> None:
    cost = estimate_cost_usd(1, 1, 1, 1)
    assert cost == round(cost, 4)
