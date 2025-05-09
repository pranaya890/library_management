from django.db import models
from django.utils import timezone

class Member(models.Model):
    name=models.CharField(max_length=100)
    email=models.EmailField(unique=True)

    membership_date=models.DateField(default=timezone.now)
     
    def __str__(self):
        return self.name
# Create your models here.
