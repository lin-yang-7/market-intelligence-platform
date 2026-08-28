from scripts.real_integration_check import percentile


def test_percentile_returns_bounded_rank() -> None:
    assert percentile([1, 2, 3, 4, 5], 95) == 5
    assert percentile([1, 2, 3, 4, 5], 50) == 3
