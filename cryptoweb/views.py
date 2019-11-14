import os
import sys
import time
import datetime

import json
import requests
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.urls import reverse

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

#from django.core import serializers

from bokeh.embed import components, json_item
from bokeh.plotting import figure, ColumnDataSource
from bokeh.resources import CDN
from bokeh.models import GeoJSONDataSource, ColumnDataSource, HoverTool, LinearColorMapper
from bokeh.embed import file_html
from bokeh.palettes import gray, inferno, plasma, PuRd

from cryptocompy import price
from cryptocompy import coin as ccoin

#from .models import

#import math

coinList = {"BTC":"orange", "XMR":"red", "ETH":"grey", "NEO":"lightgreen", "XLM":"lightblue", "LTC":"silver", "XRP":"blue", "BCH":"green"}
timeList = {"hour":{"period":"minute", "count":60},"day":{"period":"minute", "count":1440}, "week":{"period":"hour", "count":168}, "month":{"period":"hour", "count":720},"year":{"period":"day", "count":366}}
currencyList = {"USD":"USD", "EUR":"EUR", "CHF":"CHF", "BTC":"BTC"}

# retriev CMC API KEY and Django Security Key from environment or from file
try:
    API_KEY = os.environ["CMC_API_KEY"]
    print("API Key found in environment")
except KeyError:
    print("API Key Not found in environment!")
    try:
        from config import CMC_API_KEY
        API_KEY = CMC_API_KEY
        print("API Key found in config.py")
    except Exception as e:
        print("API Key Not found in config file !")
        #print(e)
        print("No API Key found! Bye!")
        sys.exit()


# retrives price data for single coin
def get_graph_data(coin, currency, period):
    times = []
    prices = []

    historical = price.get_historical_data(coin, currencyList[currency], timeList[period]["period"], info='close', aggregate=1, limit=timeList[period]["count"])
    for data in historical:
        dt = datetime.datetime.strptime(data["time"], "%Y-%m-%d %H:%M:%S")
        times.append(dt)
        if coin == currency:
            prices.append(1)
        else:
            prices.append(data["close"])
    return times, prices

# retrives top100 coins with infos from from CMC (requieres API KEY)
def get_market_data():
    url = ' https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest'
    parameters = {
      'convert':'USD',
    }
    headers = {
      'Accepts': 'application/json',
      'X-CMC_PRO_API_KEY': API_KEY,
    }

    # open session and send http request
    session = Session()
    session.headers.update(headers)

    response = session.get(url, params=parameters)
    #print(response)
    if response:
        data = json.loads(response.text)
        status = data.get("status").get("error_code")
        m_data = data.get("data")

        m_cap = m_data.get("quote").get("USD").get("total_market_cap")
        vol24 = m_data.get("quote").get("USD").get("total_volume_24h")
        btc_dom = m_data.get("btc_dominance")

        market_data = {"total_market_cap":m_cap, "total_volume":vol24, "btc_share":btc_dom}
    else:
        market_data = None
        print("Error getting market data from API.")

    #print(market_data)
    return market_data


# retrives top100 coins with infos from from CMC (requieres API KEY)
def get_coin_data(request, limit=100):

    print("Retrieving new data from API...")
    coin_list = []
    coin_data = []

    #url = 'https://api.alternative.me/v1/ticker/'
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

    parameters = {
      'start':'1',
      'limit':limit,
      'convert':'USD',
    }
    headers = {
      'Accepts': 'application/json',
      'X-CMC_PRO_API_KEY': API_KEY,
    }

    # open session and send http request
    session = Session()
    session.headers.update(headers)
    response = session.get(url, params=parameters)

    if response:
        data = json.loads(response.text)
        c_data = data["data"]
        #print(c_data)
        for item in c_data:
            coin_list.append(item.get("symbol"))

            coin_data.append({
                "symbol":item.get("symbol"),
                "name":item.get("name")[:15],
                "market_cap":round(item.get("quote").get("USD").get("market_cap")/1000000),
                "volume":round(item.get("quote").get("USD").get("volume_24h")/1000000),
                "price": "{0:.2f}".format(item.get("quote").get("USD").get("price")),
                "change_24h":("{0:.2f}".format(item.get("quote").get("USD").get("percent_change_24h"))),
                "change_1h":("{0:.2f}".format(item.get("quote").get("USD").get("percent_change_1h"))),
            })

    else:
        print("Error getting market data from API.")

    return coin_list, coin_data

### DJANGO VIEWS ###

def index(request):
    request.session["coin_data"] = None
    request.session["coin_list"] = None
    request.session["market_data"] = None
    request.session["timestamp"] = 0

    if request.user.is_authenticated:
        user = request.user
    else:
        user = False
    return render(request, "index.html", {"user":user})


def crypto(request):
    if request.user.is_authenticated:
        user = request.user
    else:
        user = False

    # do we have session data stored (avoiding too many api calls)
    try:
        print("Last data retrieved: ", request.session["timestamp"])
    except KeyError:
        request.session["timestamp"] = 0

    # sorting commands received in url or default
    try:
        sort_by = request.GET["sort_by"]
    except KeyError:
        sort_by = None

    # only retrieve data after 60 seconds
    if time.time() > request.session["timestamp"] + 60:
        market_data = get_market_data()
        coin_list, coin_data = get_coin_data(request, limit=100)
        request.session["market_data"] = market_data
        request.session["coin_data"] = coin_data
        request.session["coin_list"] = coin_list
        request.session["timestamp"] = time.time()
        print("New market data stored in session at ", request.session["timestamp"])
    else:
        print("Reading data from session...")
        market_data = request.session["market_data"]
        coin_list =request.session["coin_list"]
        coin_data = request.session["coin_data"]

    # sort data if needed (default order is by market_cap)
    if sort_by:
        print(f"Sorting data by {sort_by}...")
        rev_order = True
        if sort_by in ['symbol', 'name']:
            rev_order = False
        try:
            coin_data.sort(key=lambda x: x[sort_by], reverse=rev_order)
        except KeyError:
            print("Error sorting data!")

    resources=CDN.render()
    time_options = timeList.keys()
    currency_options = currencyList.keys()

    return render(request, "cryptoweb/crypto.html", {'resources':CDN.render(), 'options':coin_list, 'user':user, 'time_options':time_options, 'currency_options':currency_options, 'coin_data':coin_data, 'market_data': market_data})


def crypto_plot(request):
    # get input variables
    if request.user.is_authenticated:
        user = request.user
    else:
        user = False
    coin = request.GET.get('coin_option')
    period = request.GET.get('time_option')
    currency = request.GET.get('currency_option')

    if coin == None:
        coin = "BTC"
    if period == None:
        period = "day"
    if currency == None:
        currency = "USD"
    print(coin, period, currency)

    # retrive data from cryptocompy api
    times, prices = get_graph_data(coin, currency, period)

    # generate graph
    PLOT_OPTIONS = dict(plot_width=800, plot_height=300, x_axis_type='datetime')
    SCATTER_OPTIONS = dict(size=12, alpha=0.5)
    try:
        color=coinList[coin]
    except KeyError:
        color="firebrick"
    plot = figure(sizing_mode='scale_width', tools='pan', **PLOT_OPTIONS)
    #plot.scatter(x, data(), color=color, **SCATTER_OPTIONS)
    plot.line(times, prices, color=color, line_width=5)

    return HttpResponse(json.dumps(json_item(plot, "myplot")))


def login_view(request):
    if request.method == "GET":
        #return HttpResponseRedirect(reverse("index"))
        return render(request, "users/login.html", {"message": "Please enter your username and password.", "user":False})
    username = request.POST["username"]
    password = request.POST["password"]
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "users/login.html", {"message": "Invalid credentials.", "user":False})

def logout_view(request):
    logout(request)
    return render(request, "index.html", {"message": "You are now logged out.", "user":False})


def register(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))

    if request.method == "GET":
        return render(request, "users/register.html", {"message": "Please fill in the data below to register a new user.", "user":False})

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        email = request.POST["email"]


        if len(User.objects.all().filter(username=username)) > 0:
            return render(request, "error.html", {"message": "Username already in use.", "user":False})
        if len(User.objects.all().filter(email=email)) > 0:
            return render(request, "error.html", {"message": "E-mail already in use.", "user":False})

        new_user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name, email=email)
        new_user.save()
        print("User created:", username, password, first_name, last_name, email)

        user = authenticate(request, username=username, password=password)
        login(request, user)
        print(user)
        return HttpResponseRedirect(reverse("index"))
