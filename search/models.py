from django.db import models


class History(models.Model):
    text = models.CharField(max_length=255, unique=True)
    cdate = models.DateField(auto_now_add=True)

