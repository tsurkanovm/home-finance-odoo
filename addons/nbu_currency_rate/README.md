@todo - adapt to new naming and logic
# Currency Rate Update — NBU (Ukraine)

Odoo module that adds **National Bank of Ukraine (NBU)** as a currency rate
provider. Uses the **free, public NBU REST API** — no API key, no registration,
no payment.

## Why NBU instead of Minfin?

| Provider | Free? | API Key? | Official? | Notes |
|----------|-------|----------|-----------|-------|
| **NBU (bank.gov.ua)** | ✅ Completely free | ❌ Not needed | ✅ Official central bank | Best for accounting — these are the legally recognized rates in Ukraine |
| Minfin (minfin.com.ua) | ⚠️ Paid tiers | ✅ Required | ❌ Commercial aggregator | Good for market/black-market rates, but costs money and requires registration |
| ECB | ✅ Free | ❌ Not needed | ✅ Official | Does **not** include UAH |
| Frankfurter | ✅ Free | ❌ Not needed | ⚠️ Aggregator | Includes UAH via NBU data, but adds a dependency |

**Recommendation:** For Ukrainian accounting, use **NBU** — the rates are
official, legally binding for tax reporting, and the API is free forever.

## NBU API Reference

### Endpoints

```
# All currencies — latest rates
GET https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json

# All currencies — specific date
GET https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?date=20260325&json

# Single currency
GET https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=USD&json

# Single currency + date
GET https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=EUR&date=20260325&json
```

### Response format

```json
[
  {
    "r030": 840,
    "txt": "Долар США",
    "rate": 43.8288,
    "cc": "USD",
    "exchangedate": "25.03.2026"
  },
  {
    "r030": 978,
    "txt": "Євро",
    "rate": 50.8830,
    "cc": "EUR",
    "exchangedate": "25.03.2026"
  }
]
```

**`rate`** = how many UAH you get for **1 unit** of the foreign currency.

### Timing

Rates are published daily around **15:30 Kyiv time** (EET = UTC+2 / EEST = UTC+3).
Before 15:30, the API returns today's rate. After 15:30, it returns the next
business day's rate.

## Installation

1. Copy the `nbu_currency_rate` folder into your Odoo custom addons path.
2. Restart the Odoo server.
3. Go to **Apps** → Update Apps List → search "NBU" → Install.

## Configuration

1. (@todo)

Make sure your target currencies (USD, EUR, etc.) are **active** under
**Accounting → Configuration → Currencies**.

## How Odoo rates work

Odoo stores rates as the **inverse** of what NBU provides:

| If company currency is UAH | NBU says | Odoo stores |
|-----------------------------|----------|-------------|
| 1 USD = 43.83 UAH | `rate: 43.8288` | `1 / 43.8288 = 0.02281...` |
| 1 EUR = 50.88 UAH | `rate: 50.8830` | `1 / 50.8830 = 0.01965...` |

If your company currency is **not UAH** (e.g., USD), the module cross-converts:

```
Odoo rate for EUR (when company = USD):
  = UAH_per_USD / UAH_per_EUR
  = 43.8288 / 50.8830
  = 0.8613...
```

## File structure

```
currency_rate_update_ua/
├── __manifest__.py                 # Module metadata
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── res_company.py              # Core logic: NBU provider + rate parsing
├── views/
│   └── res_company_views.xml       # Added provider selector in company form
├── data/
│   └── ir_cron_data.xml            # Optional dedicated cron
├── test_nbu_api.py                 # Standalone script to test the API
└── README.md
```

## Testing without Odoo

```bash
cd currency_rate_update_ua
pip install requests
python3 test_nbu_api.py             # latest rates
python3 test_nbu_api.py 2026-03-20  # historical rates
```

## License

LGPL-3
