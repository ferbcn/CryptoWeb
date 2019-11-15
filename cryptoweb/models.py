from django.db import models
from django.contrib.auth.models import User


class Position(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="userpos")
    ticker = models.CharField(max_length=5)
    price = models.FloatField()
    quantity = models.FloatField()

    def __str__(self):
        return f"Porfolio position: {self.quantity} x {self.ticker} at price {self.price}"
