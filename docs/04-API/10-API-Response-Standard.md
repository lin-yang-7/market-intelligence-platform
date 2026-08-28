# API Response Standard

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the unified API response standard for the Market
Intelligence Platform.

All public APIs must follow the same response structure to ensure
consistency for external developers.

------------------------------------------------------------------------

# 2. Response Structure

All APIs return:

``` json
{
  "code":0,
  "message":"success",
  "serverTime":1700000000000,
  "data":{}
}
```

------------------------------------------------------------------------

# 3. Response Fields

## code

Type:

    integer

Purpose:

Indicates request result.

Example:

    0

means success.

------------------------------------------------------------------------

## message

Type:

    string

Purpose:

Human-readable message.

Example:

    success

------------------------------------------------------------------------

## serverTime

Type:

    long

Purpose:

Server timestamp in milliseconds.

------------------------------------------------------------------------

## data

Type:

    object / array

Contains business response data.

------------------------------------------------------------------------

# 4. Success Response

Example:

``` json
{
 "code":0,
 "message":"success",
 "data":{
  "symbol":"BTCUSDT",
  "price":68000
 }
}
```

------------------------------------------------------------------------

# 5. Error Response

Example:

``` json
{
 "code":1001,
 "message":"Unauthorized",
 "data":null
}
```

------------------------------------------------------------------------

# 6. HTTP Status Codes

Standard mapping:

  HTTP   Meaning
  ------ ----------------------
  200    Success
  400    Parameter error
  401    Authentication error
  403    Permission denied
  404    Resource not found
  429    Rate limit
  500    Server error

------------------------------------------------------------------------

# 7. Business Error Codes

## Authentication

  Code   Description
  ------ -------------------
  1001   Invalid API Key
  1002   Invalid Signature
  1003   Token Expired

------------------------------------------------------------------------

## Parameter

  Code   Description
  ------ -------------------
  2001   Invalid Parameter
  2002   Missing Parameter
  2003   Invalid Format

------------------------------------------------------------------------

## Market

  Code   Description
  ------ ------------------------
  3001   Symbol Not Found
  3002   Exchange Not Supported

------------------------------------------------------------------------

## Service

  Code   Description
  ------ ---------------------
  5000   Internal Error
  5001   Service Unavailable

------------------------------------------------------------------------

# 8. Pagination Standard

Large datasets use cursor pagination.

Request:

    limit

    cursor

Response:

``` json
{
 "items":[],
 "nextCursor":"xxxx"
}
```

------------------------------------------------------------------------

# 9. Time Format

All timestamps use:

    Unix milliseconds

Example:

    1700000000000

------------------------------------------------------------------------

# 10. Number Format

Price:

    Float64

Volume:

    Float64

Score:

    0-100

Percentage:

    Float

Example:

    5.25

means 5.25%.

------------------------------------------------------------------------

# 11. Empty Data Handling

No result:

``` json
{
 "code":0,
 "data":[]
}
```

Never return:

    null

for collection data.

------------------------------------------------------------------------

# 12. Version Compatibility

API versions:

    /v1/

    /v2/

Rules:

-   Do not break existing fields
-   Add fields backward compatible
-   Deprecate before removal

------------------------------------------------------------------------

# 13. Request ID

All responses may include:

    requestId

Purpose:

-   Debugging
-   Support tracking
-   Log correlation

------------------------------------------------------------------------

# 14. API Documentation Requirements

Every endpoint must define:

-   URL
-   Method
-   Parameters
-   Response
-   Error codes
-   Rate limits

------------------------------------------------------------------------

# 15. Future Extensions

Reserved:

-   GraphQL response format
-   Streaming response standard
-   AI explanation schema

------------------------------------------------------------------------

# 16. Compliance

All APIs must follow:

-   Unified response format
-   Error code standard
-   Version strategy
-   Timestamp standard

This document defines the official API response standard.
