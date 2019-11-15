# CryptoX

## Description
- Website dedicated to cryptocurrency price data display using different free APIs (rate limits apply, use with care)
- Python Django backend using javascript, Bootstrap4 and CSS styling for a more or less mobile responsive user interface
- DB driven user access and storage of user generated portfolio data
- Graphical Price info generated with bokeh library https://docs.bokeh.org/en/latest/.

![screenshot](cryptox.png)

## Features

### Crypto:
- use of different APIs
- data retrieval, date&time manipulation, string formatting
- Responsive Charts generated with Bokeh
- Responsive data tables (hide columns on small screens)
- Main price data is retrieved from CMC API (https://coinmarketcap.com/api/)
- Data is cached locally and retrieved from APIs every 60 seconds the most
- Data for price graphs uses cryptocompy library by ttstieger (https://github.com/ttsteiger/cryptocompy), prices are pulled from (Cryptocompare API: https://www.cryptocompare.com/api)

### User Database
- sqlite3 (saved locally)
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
