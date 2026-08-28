from .schemas import ScreenerPreset

SCREENER_PRESETS: dict[str, ScreenerPreset] = {
    "long_inflow_v1": ScreenerPreset(
        id="long_inflow_v1",
        name="Long Inflow Alert",
        type="longInflow",
    ),
    "momentum_v1": ScreenerPreset(
        id="momentum_v1",
        name="Momentum Screening",
        type="momentum",
    ),
    "volume_v1": ScreenerPreset(
        id="volume_v1",
        name="Volume Activity Screening",
        type="volume",
    ),
}

