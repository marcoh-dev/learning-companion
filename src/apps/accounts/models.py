from django.conf import settings
from django.db import models


class Cohort(models.TextChoices):
    SPRING_2026 = '2026-spring', '2026 Spring'
    AUTUMN_2026 = '2026-autumn', '2026 Autumn'
    SPRING_2027 = '2027-spring', '2027 Spring'


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile'
    )
    name = models.CharField(max_length=100, blank=True)
    cohort = models.CharField(max_length=20, choices=Cohort, blank=True)
