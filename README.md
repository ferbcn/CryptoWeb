# CryptoWeb

## Description
- Website dedicated to cryptocurrency price display using different free APIs (rate limits apply, use with responsability) 
- Mobile responsive website and graphical elements
- DB driven user access and storage of user generated data

![screenshot](cryptox.png)
## Features & Challenges
### Python Django backend
  - User creation and identification
  - Sqlite3 DB for user portfolio

### Crypto:
- use of different APIs
- data retrieval, date&time manipulation, string formating
- Responsive Charts generated with Bokeh
- Responsive data tables (hide columns on small screens)
- Data is chahed locally and retrieved from APIs every 60 seconds the most

### User Database
- user portfolio with price retrieval and editing features
- total price and value infos

### To Think:
- price notifications system
- portfolio grsafical analysis and data 

## Description
1. Install dependencies: cryptomcompy (https://github.com/ttsteiger/cryptocompy) uses this free api (Cryptocompare API: https://www.cryptocompare.com/api)
2. Additionally a CMC API KEY is needed for retrieval of some data (https://coinmarketcap.com/api/)
3. For security reasons Djangos's SECURITY KEY has to be loaded from environment or from config.py file (not included)
