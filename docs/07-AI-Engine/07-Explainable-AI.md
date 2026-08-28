# Explainable AI

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

Defines explainable AI capabilities for the Market Intelligence
Platform.

The goal is to make AI decisions understandable.

------------------------------------------------------------------------

# 2. XAI Role

Architecture:

    AI Prediction

    ↓

    Explanation Engine

    ↓

    User Interface

------------------------------------------------------------------------

# 3. Explanation Output

Each AI result provides:

-   Prediction
-   Confidence
-   Main factors
-   Risk factors
-   Feature contribution

------------------------------------------------------------------------

# 4. Feature Contribution

Example:

``` json
{
 "score":92,
 "factors":{
  "capital_flow":40,
  "volume":30,
  "momentum":22
 }
}
```

------------------------------------------------------------------------

# 5. Explanation Methods

Supported:

-   Feature importance
-   Contribution analysis
-   Historical comparison

Future:

-   SHAP
-   LIME

------------------------------------------------------------------------

# 6. Signal Explanation

For Long Inflow:

Shows:

-   Why selected
-   Which factors triggered
-   Confidence level

------------------------------------------------------------------------

# 7. User Benefits

Provides:

-   Trust
-   Transparency
-   Better decisions

------------------------------------------------------------------------

# 8. Monitoring

Track:

-   Explanation consistency
-   Feature impact changes
-   Model drift

------------------------------------------------------------------------

# 9. Future Extensions

-   AI analyst assistant
-   Natural language explanation
-   Interactive analysis
