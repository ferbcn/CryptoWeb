from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("crypto_plot", views.crypto_plot, name="plot"),
    path("crypto", views.crypto, name="data"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    
]
