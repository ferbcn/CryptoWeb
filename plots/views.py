from os import path
import time
import datetime
import csv
import json
import requests
import urllib.request

from bs4 import BeautifulSoup

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.urls import reverse

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from django.core import serializers

from bokeh.embed import components, json_item
from bokeh.plotting import figure, ColumnDataSource
from bokeh.resources import CDN
from bokeh.models import GeoJSONDataSource, ColumnDataSource, HoverTool, LinearColorMapper
from bokeh.embed import file_html
from bokeh.palettes import gray, inferno, plasma, PuRd

import numpy as np

from cryptocompy import price
from cryptocompy import coin as ccoin

from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from io import BytesIO
import base64

import uuid

#from .models import 

import math

coinList = {"BTC":"orange", "XMR":"red", "ETH":"grey", "NEO":"green"}
timeList = {"hour":{"period":"minute", "count":60},"day":{"period":"minute", "count":1440}, "week":{"period":"hour", "count":168}, "month":{"period":"hour", "count":720},"year":{"period":"day", "count":366}}
currencyList = {"USD":"USD", "EUR":"EUR", "CHF":"CHF", "BTC":"BTC"}
colorOptions = ["Reds", "Blues", "Greens"]


def index(request):
    if request.user.is_authenticated:
        user = request.user
    else:
        user = False
    return render(request, "index.html", {"user":user})

def CoinMarketCapGetCoins(limit=100):
    from requests import Request, Session
    from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
    import json

    #url = 'https://api.alternative.me/v1/ticker/'
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

    parameters = {
      'start':'1',
      'limit':limit,
      'convert':'USD'
    }
    headers = {
      'Accepts': 'application/json',
      'X-CMC_PRO_API_KEY': '59454a97-d622-41b7-b70c-e2bec471a159',
    }

    session = Session()
    session.headers.update(headers)

    coins = []
    coin_data = []

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        c_data = data["data"]
        #print(c_data)
        for item in c_data:
            coins.append(item.get("symbol"))

            coin_data.append({
            "symbol":item.get("symbol"),
            "name":item.get("name"),
            "market_cap":f'{round(item.get("quote").get("USD").get("market_cap")/1000000):,}',
            "volume":f'{round(item.get("quote").get("USD").get("volume_24h")/1000000):,}',
            "price": "{0:.2f}".format(item.get("quote").get("USD").get("price")),
            "change_24h":("{0:.2f}".format(item.get("quote").get("USD").get("percent_change_24h"))),
            "change_1h":("{0:.2f}".format(item.get("quote").get("USD").get("percent_change_1h"))),
            })

        #print(coin_data)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
      print(e)

    return coins, coin_data


def crypto(request):
    if request.user.is_authenticated:
        user = request.user
    else:
        user = False
    resources=CDN.render()
    #coin_options = list(coinList.keys()) + list(ccoin.get_coin_list(coins='all').keys())[:50]
    time_options = timeList.keys()
    currency_options = currencyList.keys()
    coin_options, coin_data = CoinMarketCapGetCoins(limit=100)

    return render(request, "plots/plots.html", {'resources':CDN.render(), 'options':coin_options, 'user':user, 'time_options':time_options, 'currency_options':currency_options, 'coin_data':coin_data})

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
