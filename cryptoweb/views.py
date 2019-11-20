import os
import sys
import time
import datetime
import random

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

from .models import Position

#import math

coinList = {"BTC":"orange", "XMR":"red", "ETH":"grey", "NEO":"lightgreen", "XLM":"lightblue", "LTC":"silver", "XRP":"blue", "BCH":"green"}
timeList = {"day":{"period":"minute", "count":1440}, "hour":{"period":"minute", "count":60}, "week":{"period":"hour", "count":168}, "month":{"period":"hour", "count":720},"year":{"period":"day", "count":366}}
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
    historical = price.get_historical_data(coin, currency, timeList[period]["period"], info='close', aggregate=1, limit=timeList[period]["count"])
    for data in historical:
        dt = datetime.datetime.strptime(data["time"], "%Y-%m-%d %H:%M:%S")
        times.append(dt)
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

        m_cap = '{:,}'.format(round(m_data.get("quote").get("USD").get("total_market_cap")/1000000))
        vol24 = '{:,}'.format(round(m_data.get("quote").get("USD").get("total_volume_24h")/1000000))
        btc_dom = '{:.1%}'.format(m_data.get("btc_dominance")/100)

        market_data = {"total_market_cap":m_cap, "total_volume":vol24, "btc_share":btc_dom}
    else:
        market_data = None
        print("Error getting market data from API.")

    #print(market_data)
    return market_data

def float2str(num):
    if num >= 1000:
        num_str = "{0:.2f}".format(num)
    elif num >= 100:
        num_str = "{0:.3f}".format(num)
    elif num >= 10:
        num_str = "{0:.4f}".format(num)
    else:
        num_str = "{0:.5f}".format(num)
    return num_str

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
            coin_list.append({"ticker":item.get("symbol"), "name":item.get("name")})
            coin_data.append({
                "symbol":item.get("symbol"),
                "name":item.get("name")[:15],
                "cmc_rank":item.get("cmc_rank"),
                "market_cap":round(item.get("quote").get("USD").get("market_cap")/1000000),
                "volume":round(item.get("quote").get("USD").get("volume_24h")/1000000),
                "market_cap_str":'{:,}'.format(round(item.get("quote").get("USD").get("market_cap")/1000000)),
                "volume_str":'{:,}'.format(round(item.get("quote").get("USD").get("volume_24h")/1000000)),
                "price": item.get("quote").get("USD").get("price"),
                "price_str": float2str(float(item.get("quote").get("USD").get("price"))),
                "change_24h":("{0:.2f}".format(item.get("quote").get("USD").get("percent_change_24h"))),
                "change_1h":("{0:.2f}".format(item.get("quote").get("USD").get("percent_change_1h"))),
            })
    # no response from API
    else:
        print("Error getting market data from API.")

    return coin_list, coin_data


def retrieve_data_session_or_new_api(request):
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

    return coin_list, coin_data, market_data


### Operations on user DB (portfolio management) ###

# retrieve portfolio positions from user DB
def get_user_portfolio(user, coin_data):
    positions = Position.objects.all().filter(user=user)
    #print(positions)
    positions_price_value = []
    total_portfolio_value = 0
    total_purchase_value = 0
    for pos in positions:
        id = pos.id
        ticker = pos.ticker.upper()
        quantity = pos.quantity
        pprice = pos.price
        #print(coin_data)
        for coin in coin_data:
            if ticker == coin.get("symbol"):
                cprice = float(coin.get("price"))
                break
            cprice = 0
        pvalue = float(pprice * quantity)
        cvalue = float(cprice * quantity)
        try:
            cperf = "{0:.2f}".format((cvalue / pvalue - 1) * 100)
        except ZeroDivisionError:
            cperf = 0
        total_portfolio_value += cvalue
        total_purchase_value += pvalue
        #append the data to our custom portfolio list object
        positions_price_value.append({"id": id, "ticker": ticker, "quantity":quantity, "pprice": float2str(pprice), "cprice":float2str(cprice), "cvalue":float2str(cvalue), "cperf":cperf})

    #reformat total values
    total_purchase_value_str = '{:,}'.format(round(total_purchase_value))

    total_portfolio_value_str = '{:,}'.format(float("{0:.2f}".format(total_portfolio_value)))
    #print(positions_price_value, total_portfolio_value)
    # catch division by zero
    try:
        total_var =  "{0:.2f}".format((float(total_portfolio_value) / float(total_purchase_value) - 1) * 100)
    except ZeroDivisionError:
        total_var = 0
    return positions_price_value, total_purchase_value_str, total_portfolio_value_str, total_var

# add position to user portfolio in DB
def add_position(user, ticker, quantity, price):
    # save game to DB
    try:
        position = Position(user=user, ticker=ticker, price=price, quantity=quantity)
        position.save()
        return True
    except Exception as e:
        print(e)
        return False


#remove a position from portfolio
def remove_position(user, pos_id):
    print("Removing position...")
    # save game to DB
    try:
        position_obj = Position.objects.get(pk=pos_id)
        if position_obj.user == user:
            position_obj.delete()
            return True
        else:
            return False
    except Exception as e:
        print (e)
        return False


def fetch_current_price (request, ticker):
    price = 0
    return price


### DJANGO VIEWS ###

# deafualt view (landing page), resets session varaibles (allows fror fetch of fresh data)
def index(request):
    # reset session variables (used for locally storing data reducing api calls)
    request.session["coin_data"] = None
    request.session["coin_list"] = None
    request.session["market_data"] = None
    request.session["timestamp"] = 0

    if request.user.is_authenticated:
        user = request.user
    else:
        user = False
    return HttpResponseRedirect(reverse("crypto"))


def portfolio(request):

    if request.user.is_authenticated:
        user = request.user
    else:
        user = False
        return render(request, "error.html", {"user":user, "message":"Please login first to access portfolio functionality!"})

    coin_list, coin_data, market_data = retrieve_data_session_or_new_api(request)

    user_portfolio, total_purchase_value, total_value, total_var = get_user_portfolio(user, coin_data)


    return render(request, "cryptoweb/portfolio.html", {"user":user, "user_portfolio":user_portfolio, "total_value":total_value, "total_purchase_value":total_purchase_value, 'performance':total_var, 'crypto_options':coin_list, 'coin_data':coin_data})


def edit_portfolio(request):

    if request.user.is_authenticated:
        user = request.user
    else:
        user = False
        return render(request, "error.html", {"user":user, "message":"Please login first to access portfolio functionality!"})

    if request.method == "POST":
        # retrieve data from POST request
        ticker = request.POST["ticker"]
        quantity = float(request.POST["quantity"])
        price = float(request.POST["price"])
        print(f"Adding Position {ticker}, {quantity} @ {price}...")
        if add_position(user, ticker, quantity, price):
            print(f"Position added.")
        else:
            print(f"Could NOT add position!")
        return HttpResponseRedirect(reverse("portfolio"))

    if request.method == "GET":
        # retrieve data from POST request, are we deleting a position
        try:
            delete_item = request.GET["delete"]
        except KeyError:
            delete_item = False

        if delete_item:
            print(f"Removing position id: {delete_item}...")
            if remove_position(user, delete_item):
                print(f"Position with ID: {delete_item} deleted!")
            else:
                print(f"Position with ID: {delete_item} NOT deleted!")

        return HttpResponseRedirect(reverse("portfolio"))


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

    coin_list, coin_data, market_data = retrieve_data_session_or_new_api(request)

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

    return render(request, "cryptoweb/crypto.html", {'resources':CDN.render(), 'crypto_options':coin_list, 'user':user, 'time_options':time_options, 'currency_options':currency_options, 'coin_data':coin_data, 'market_data': market_data})


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
        try:
            email = request.POST["email"]
        except KeyError:
            email = username

        # check for unique username
        if len(User.objects.all().filter(username=username)) > 0:
            return render(request, "error.html", {"message": "Username already in use.", "user":False})

        new_user = User.objects.create_user(username=username, password=password, email=email)
        new_user.save()
        print("User created:", username, password, email)

        user = authenticate(request, username=username, password=password)
        login(request, user)
        print("Logged in as: ", user)
        return HttpResponseRedirect(reverse("index"))
