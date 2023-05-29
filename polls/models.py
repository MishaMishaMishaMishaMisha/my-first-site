from django.db import models
import datetime
from django.utils import timezone


class Dashboard(models.Model):
    dashboard_name = models.CharField(max_length=200)
    dashboard_key = models.CharField(max_length=200)
    user_ip = models.CharField(max_length=200)
    cr_date = models.DateTimeField('date created')

    def __str__(self):
        return self.dashboard_name


class Question(models.Model):
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE)
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes_yes = models.IntegerField(default=0)

    user_ip = models.CharField(max_length=200)

    def __str__(self):
        return self.choice_text


class UserChoice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user_ip = models.CharField(max_length=200)
    choice = models.CharField(max_length=200)

    def __str__(self):
        return self.user_ip






