# Data Dictionary

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the unified data dictionary standards for the
Market Intelligence Platform.

It provides:

-   Field definitions
-   Data types
-   Naming conventions
-   Data ownership
-   Data sources
-   Lifecycle rules

------------------------------------------------------------------------

# 2. Data Naming Standards

## Database Naming

Use:

    snake_case

Examples:

    created_at

    updated_at

    symbol

------------------------------------------------------------------------

## Time Fields

Standard:

    created_at

    updated_at

    timestamp

Format:

UTC timezone

------------------------------------------------------------------------

## Identifier Fields

Primary identifiers:

    id

External identifiers:

    *_id

Examples:

    user_id

    signal_id

    trade_id

------------------------------------------------------------------------

# 3. Common Data Types

  Purpose         Type
  --------------- -----------------
  ID              bigint / UUID
  Name            varchar
  Status          varchar
  Amount          decimal / float
  Time            datetime
  Configuration   json

------------------------------------------------------------------------

# 4. MySQL Data Dictionary

## users

Purpose:

Store user accounts.

Fields:

  Field           Description
  --------------- -----------------
  id              User identifier
  email           Login account
  password_hash   Password hash
  status          Account status
  created_at      Creation time
  updated_at      Update time

------------------------------------------------------------------------

## api_keys

Purpose:

External API authentication.

Fields:

  Field         Description
  ------------- -----------------
  id            Key identifier
  user_id       Owner
  api_key       Public key
  secret_hash   Secret hash
  permissions   API permissions
  expires_at    Expiration

------------------------------------------------------------------------

## subscriptions

Purpose:

User subscription information.

Fields:

  Field        Description
  ------------ ---------------------
  id           Subscription ID
  user_id      User
  plan_id      Plan
  status       Subscription status
  start_time   Start
  end_time     End

------------------------------------------------------------------------

## alert_rules

Purpose:

User alert configuration.

Fields:

  Field        Description
  ------------ -----------------
  id           Rule ID
  user_id      Owner
  rule_type    Alert type
  conditions   Rule conditions
  enabled      Active status

------------------------------------------------------------------------

# 5. ClickHouse Data Dictionary

## market_kline

Purpose:

Historical candle data.

Fields:

  Field       Description
  ----------- -----------------
  exchange    Exchange name
  symbol      Trading pair
  interval    Candle interval
  open        Open price
  high        Highest price
  low         Lowest price
  close       Closing price
  volume      Trading volume
  timestamp   Candle time

------------------------------------------------------------------------

## market_trade

Purpose:

Trade history.

Fields:

  Field       Description
  ----------- -------------------
  exchange    Exchange
  symbol      Trading pair
  trade_id    Exchange trade ID
  price       Trade price
  quantity    Trade quantity
  side        Buy or sell
  timestamp   Trade time

------------------------------------------------------------------------

## feature_history

Purpose:

Quantitative feature storage.

Fields:

  Field           Description
  --------------- ------------------
  symbol          Trading pair
  feature_name    Feature name
  feature_value   Calculated value
  version         Feature version
  timestamp       Calculation time

------------------------------------------------------------------------

## signal_history

Purpose:

Signal records.

Fields:

  Field         Description
  ------------- -----------------
  signal_id     Signal ID
  symbol        Trading pair
  signal_type   Signal category
  score         Signal score
  confidence    Confidence
  reason        Explanation
  timestamp     Creation time

------------------------------------------------------------------------

# 6. Redis Data Dictionary

## market:ticker:{symbol}

Contains:

-   price
-   bid
-   ask
-   volume
-   timestamp

------------------------------------------------------------------------

## ranking:{type}

Contains:

-   symbol
-   score
-   rank
-   update_time

------------------------------------------------------------------------

## feature:{symbol}:{name}

Contains:

-   feature_value
-   version
-   timestamp

------------------------------------------------------------------------

## signal:latest

Contains:

-   signal_id
-   symbol
-   signal_type
-   score
-   confidence

------------------------------------------------------------------------

# 7. Data Source Mapping

  Data          Source
  ------------- ----------------
  Market Data   Exchange APIs
  User Data     Platform
  Features      Feature Engine
  Signals       Signal Engine
  Rankings      Ranking Engine

------------------------------------------------------------------------

# 8. Data Lifecycle

## Real-time Data

Storage:

Redis

Retention:

Short term

------------------------------------------------------------------------

## Business Data

Storage:

MySQL

Retention:

Long term

------------------------------------------------------------------------

## Analytical Data

Storage:

ClickHouse

Retention:

Based on policy

------------------------------------------------------------------------

# 9. Data Quality Rules

All data should validate:

-   Required fields
-   Data type
-   Timestamp
-   Source
-   Version

------------------------------------------------------------------------

# 10. Future Extensions

Reserved:

-   AI Feature Dictionary
-   Data Marketplace Dictionary
-   External API Schema Registry

------------------------------------------------------------------------

# 11. Compliance

Every new data field must define:

-   Name
-   Type
-   Meaning
-   Owner
-   Source
-   Lifecycle

This document defines the platform data dictionary standard.
