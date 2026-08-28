# Market Intelligence Python SDK

MVP Python SDK for the Market Intelligence Platform API Gateway.

```python
from market_intelligence import Client

client = Client(base_url="http://localhost:8000", api_key="your-api-key")

ranking = client.ranking.long_inflow(limit=10)
signals = client.signal.current()
```

## Authentication

API key authentication:

```python
client = Client(api_key="ms_live_xxx")
```

User login:

```python
client = Client()
client.user.login("demo@example.com", "password123")
profile = client.user.profile()
```

## Resource Groups

- `market`
- `feature`
- `feature_store`
- `ranking`
- `screener`
- `signal`
- `alert`
- `history`
- `score`
- `rule`
- `user`

The SDK converts service errors into typed exceptions such as
`AuthenticationError`, `RateLimitError`, `ParameterError`, and `ServerError`.
