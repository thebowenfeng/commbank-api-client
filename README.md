# Commbank API Client

A fully asynchronous (unofficial) python API client for the [Commonwealth Bank of Australia](https://www.commbank.com.au).

## Install

The following libraries are required:
- `beautifulsoup4` (bs4)
- `aiohttp`

The following libraries are recommended:
- `asyncio` (to run asynchronous code)

[Install via PyPI](https://pypi.org/project/commbank-api-client/)

## Documentation

For sample usages, see `main.py`

For type documentation, see `commbank-api-client/types.py`. Note that the unique identifier for a transaction can be either `Transaction.id` or `Transaction.transaction_details_request`.
Some transactions do not have an ID, so transaction_details_request is used instead to uniquely identify said transaction, and vice versa. Each transaction is identified by one or the other.
