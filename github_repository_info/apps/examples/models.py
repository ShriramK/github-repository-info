from django.db import models


# Create your models here.
class Repos(models.Model):
    repo_user_id = models.IntegerField(default=0)
    repo_names = models.JSONField(default='')
    avatar_url = models.TextField(default='')
    fetched_time = models.IntegerField(default=0)
