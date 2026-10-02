from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)
    # Curated starter set, offered to every user (seeded by a data migration).
    starter = models.BooleanField(default=False)
