from django.db import models
from django.contrib.auth.models import User

"""
# Create your models here.
class Wordcloud(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")
    cloud_id = models.CharField(max_length=64)
    url = models.CharField(max_length=128)
    timestamp = models.IntegerField()

    def __str__(self):
        return f"Wordcloud Object: {self.cloud_id} for website: {self.url}, user: {self.user} (timestamp: {self.timestamp})"

class OpenMapPOI(models.Model):
    tag_key = models.CharField(max_length=32)
    tag_value = models.CharField(max_length=32)
    country_code = models.CharField(max_length=2)
    name = models.CharField(max_length=128)
    long = models.FloatField()
    lat = models.FloatField()

    def __str__(self):
        return f"POI: {self.name} - {self.lat} / {self.long}"
"""
