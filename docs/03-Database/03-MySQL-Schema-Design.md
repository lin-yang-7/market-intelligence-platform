# MySQL Schema Design

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the MySQL table design for the Market Intelligence
Platform.

The schema focuses on business data, user management, permissions,
subscriptions, alerts, and platform configuration.

------------------------------------------------------------------------

# 2. Schema Design Principles

All tables follow:

-   Clear ownership
-   Consistent naming
-   UUID or distributed ID strategy
-   Audit fields
-   Migration management
-   Proper indexing

------------------------------------------------------------------------

# 3. Common Table Fields

Most business tables include:

``` sql
id

created_at

updated_at

status
```

Optional:

``` sql
deleted_at
```

------------------------------------------------------------------------

# 4. User Domain

## users

Purpose:

Store account authentication information.

Fields:

  Field           Type       Description
  --------------- ---------- ----------------
  id              bigint     Primary key
  email           varchar    Login email
  password_hash   varchar    Password hash
  status          varchar    Account status
  created_at      datetime   Creation time
  updated_at      datetime   Update time

Indexes:

-   unique(email)
-   status

------------------------------------------------------------------------

## user_profiles

Purpose:

Store user profile information.

Fields:

  Field      Type      Description
  ---------- --------- ----------------
  id         bigint    Primary key
  user_id    bigint    User reference
  nickname   varchar   Display name
  avatar     varchar   Avatar URL
  timezone   varchar   User timezone

Indexes:

-   user_id

------------------------------------------------------------------------

# 5. API Management Domain

## api_keys

Purpose:

Manage external API access.

Fields:

  Field         Type       Description
  ------------- ---------- -----------------
  id            bigint     Primary key
  user_id       bigint     Owner
  api_key       varchar    Public key
  secret_hash   varchar    Secret hash
  permissions   json       API permissions
  expires_at    datetime   Expiration

Indexes:

-   user_id
-   api_key

------------------------------------------------------------------------

## api_usage_records

Purpose:

Track API consumption.

Fields:

  Field           Type
  --------------- ----------
  id              bigint
  api_key_id      bigint
  endpoint        varchar
  request_count   bigint
  request_time    datetime

Indexes:

-   api_key_id
-   request_time

------------------------------------------------------------------------

# 6. Subscription Domain

## subscription_plans

Purpose:

Define subscription products.

Fields:

-   id
-   name
-   price
-   api_limit
-   feature_limits
-   status

------------------------------------------------------------------------

## subscriptions

Purpose:

Store user subscriptions.

Fields:

  Field        Type
  ------------ ----------
  id           bigint
  user_id      bigint
  plan_id      bigint
  start_time   datetime
  end_time     datetime
  status       varchar

Indexes:

-   user_id
-   status

------------------------------------------------------------------------

# 7. Permission Domain

## roles

Purpose:

Define system roles.

Examples:

-   user
-   pro_user
-   enterprise
-   admin

Fields:

-   id
-   name
-   description

------------------------------------------------------------------------

## permissions

Purpose:

Define system permissions.

Fields:

-   id
-   code
-   description

------------------------------------------------------------------------

## role_permissions

Purpose:

Role permission mapping.

Fields:

-   role_id
-   permission_id

------------------------------------------------------------------------

## user_roles

Purpose:

User role mapping.

Fields:

-   user_id
-   role_id

------------------------------------------------------------------------

# 8. Alert Domain

## alert_rules

Purpose:

Store user alert conditions.

Fields:

  Field        Type
  ------------ ---------
  id           bigint
  user_id      bigint
  name         varchar
  rule_type    varchar
  conditions   json
  enabled      boolean

Indexes:

-   user_id
-   enabled

------------------------------------------------------------------------

## alert_history

Purpose:

Store triggered alerts.

Fields:

-   id
-   alert_rule_id
-   symbol
-   trigger_data
-   created_at

Indexes:

-   alert_rule_id
-   created_at

------------------------------------------------------------------------

# 9. Audit Domain

## audit_logs

Purpose:

Record security and administrative actions.

Fields:

-   id
-   user_id
-   action
-   resource
-   ip_address
-   created_at

Indexes:

-   user_id
-   created_at

------------------------------------------------------------------------

# 10. Configuration Domain

## system_config

Purpose:

Store platform configuration.

Fields:

-   id
-   config_key
-   config_value
-   description

Indexes:

-   config_key

------------------------------------------------------------------------

# 11. Database Relationship Overview

    users

     |

     +-- user_profiles

     |

     +-- api_keys

     |

     +-- subscriptions

     |

     +-- alert_rules

     |

     +-- roles

------------------------------------------------------------------------

# 12. Migration Requirements

All schema changes require:

-   Migration file
-   Review
-   Testing
-   Rollback plan

------------------------------------------------------------------------

# 13. Future Extensions

Reserved:

-   Organization tables
-   Enterprise billing
-   Data marketplace
-   API marketplace

------------------------------------------------------------------------

# 14. Compliance

Every table must define:

-   Business owner
-   Purpose
-   Fields
-   Indexes
-   Migration strategy

This document defines the MySQL business schema baseline.
