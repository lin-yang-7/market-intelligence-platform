from .schemas import FeatureDefinition

FEATURE_DEFINITIONS: dict[str, FeatureDefinition] = {
    "last_price": FeatureDefinition(
        name="last_price",
        category="market",
        version="v1",
        description="Latest traded price from the source ticker.",
        updateInterval="realtime",
    ),
    "price_momentum": FeatureDefinition(
        name="price_momentum",
        category="market",
        version="v1",
        description="24h price change percentage normalized as a momentum feature.",
        updateInterval="realtime",
    ),
    "volume_activity": FeatureDefinition(
        name="volume_activity",
        category="volume",
        version="v1",
        description="24h quote volume scaled into a 0-100 activity feature.",
        updateInterval="realtime",
    ),
    "long_inflow_score": FeatureDefinition(
        name="long_inflow_score",
        category="capital_flow",
        version="v1",
        description="MVP long-side opportunity score from positive momentum and volume activity.",
        updateInterval="realtime",
    ),
    "main_force_net_inflow": FeatureDefinition(
        name="main_force_net_inflow",
        category="capital_flow",
        version="v1",
        description=(
            "Estimated main-force net inflow derived from ticker volume and long inflow score."
        ),
        updateInterval="realtime",
    ),
    "main_force_ratio": FeatureDefinition(
        name="main_force_ratio",
        category="capital_flow",
        version="v1",
        description=(
            "Main-force pressure/support adjustment ratio, bounded to the 20-30 strategy band."
        ),
        updateInterval="realtime",
    ),
    "support_level": FeatureDefinition(
        name="support_level",
        category="price_level",
        version="v1",
        description=(
            "Estimated main-force support level from latest price and capital flow pressure."
        ),
        updateInterval="realtime",
    ),
    "resistance_level": FeatureDefinition(
        name="resistance_level",
        category="price_level",
        version="v1",
        description=(
            "Estimated main-force resistance level from latest price and capital flow pressure."
        ),
        updateInterval="realtime",
    ),
    "funding_pressure": FeatureDefinition(
        name="funding_pressure",
        category="derivatives",
        version="v1",
        description="Perpetual funding pressure scaled from funding rate into a 0-100 range.",
        updateInterval="realtime",
    ),
    "open_interest_change": FeatureDefinition(
        name="open_interest_change",
        category="derivatives",
        version="v1",
        description="Open interest change rate from perpetual contract market data.",
        updateInterval="realtime",
    ),
    "liquidation_pressure": FeatureDefinition(
        name="liquidation_pressure",
        category="derivatives",
        version="v1",
        description=(
            "Directional liquidation pressure derived from long and short liquidation value."
        ),
        updateInterval="realtime",
    ),
    "taker_buy_sell_imbalance": FeatureDefinition(
        name="taker_buy_sell_imbalance",
        category="derivatives",
        version="v1",
        description="Active buy/sell imbalance estimated from recent trade notional.",
        updateInterval="realtime",
    ),
}
