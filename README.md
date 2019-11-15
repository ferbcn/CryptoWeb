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
- data retrieval, date&time manipulation, string formatting
- Responsive Charts generated with Bokeh
- Responsive data tables (hide columns on small screens)
- Main price data is retrieved from CMC API (https://coinmarketcap.com/api/)
- Data is cached locally and retrieved from APIs every 60 seconds the most
- Data for price graphs uses cryptocompy library by ttstieger (https://github.com/ttsteiger/cryptocompy), prices are pulled from (Cryptocompare API: https://www.cryptocompare.com/api)

### User Database
- user portfolio with price retrieval and editing features
- total price and value infos

### To Think:
- price notifications system
- portfolio graphical analysis and data

## Usage
1. Install dependencies with pip: for example "pip3 install -r requirements.txt" (you may want to use a virtual environment here)
2. Apply Django migrations to Database: "python3 manage.py makemigrations", "python3 manage.py migrate"
3. Fire up a local server with: "python3 manage.py runserver 0.0.0.0:8000" or deploy somewhere.
4. Additionally a CMC API KEY is needed for retrieval of some data (https://coinmarketcap.com/api/)... if you don't want that there are other alternatives (google is your friend)
5. For security reasons Djangos's SECURITY KEY has to be loaded from environment or from config.py file (not included)
