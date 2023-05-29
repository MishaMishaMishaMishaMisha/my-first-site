from django.contrib.auth import logout, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views.generic import CreateView

from .forms import RegisterUserForm
from .models import Question, Choice, Dashboard
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from django.core import serializers
import hashlib

import random
import string


def get_client_ip(request):
    if request.user.is_authenticated:
        return request.user.username

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    #return ip
    return hashlib.sha256(ip.encode()).hexdigest()


def mainPage(request):
    #dashboards = Dashboard.objects.all()
    dashboards = Dashboard.objects.filter(user_ip=get_client_ip(request))
    return render(request, 'polls/mainpage.html', {'list': dashboards})

def createDashboard(request):

    dashboard_keys = Dashboard.objects.values_list('dashboard_key', flat=True)
    key_len = 10
    key = ""
    letters = string.ascii_letters + string.digits
    while True:

        key = ''.join(random.choice(letters) for _ in range(key_len))
        if key not in dashboard_keys:
            break


    d = Dashboard(dashboard_name=request.POST['name'], dashboard_key=key, user_ip=get_client_ip(request), cr_date=timezone.now())
    d.save()
    return HttpResponseRedirect(reverse('polls:index', args=(d.id,)))

def index(request, dashboard_id):

    ip = get_client_ip(request)
    dashboard = get_object_or_404(Dashboard, pk=dashboard_id)

    user = 0 # guest
    if ip == dashboard.user_ip:
        user = 1 # creator

    latest_question_list = Question.objects.filter(dashboard=dashboard)
    chart_data = []
    for question in latest_question_list:
        choices = question.choice_set.all()
        data = []
        labels = []
        for choice in choices:
            labels.append(choice.choice_text)
            data.append(choice.votes_yes)
        total_votes = sum(data)
        if total_votes == 0:
            percentages = [0 for d in data]
        else:
            percentages = [round((d / total_votes) * 100) for d in data]

        newLabels = []
        for i in range(len(labels)):
            new_item = labels[i] + " - " + str(percentages[i]) + "%"
            newLabels.append(new_item)

        chart_data.append({'question': question.question_text, 'question_id': question.id, 'labels': newLabels, 'data': percentages, 'total_votes': total_votes})

    #latest_question_list = Question.objects.all()
    context = {'latest_question_list': latest_question_list, 'dashboard': dashboard, 'chart_data': chart_data, 'user': user, 'ip': user}
    return render(request, 'polls/polls_list.html', context)


def find_dashboard(request):
    if request.method == 'POST':
        dashboard_key = request.POST.get('dashboard_key')
        dashboard = Dashboard.objects.filter(dashboard_key=dashboard_key).first()

        if dashboard:
            if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                # Если это AJAX-запрос, возвращаем успешный JSON-ответ с идентификатором дашбоарда
                return JsonResponse({'success': True, 'redirect_url': f'/{dashboard.id}/'})
            else:
                # Если это обычный POST-запрос, делаем перенаправление на представление index с передачей идентификатора дашбоарда
                return HttpResponseRedirect(reverse('polls:index', args=(dashboard.id,)))

        # Если ключ неправильный, возвращаем JSON-ответ с сообщением об ошибке
        return JsonResponse({'success': False, 'error_message': 'Дашбоард з таким ключем не знайдено'})

    # В случае GET-запроса или не AJAX-запроса делаем перенаправление
    return HttpResponseRedirect(reverse('polls:mainPage'))


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'polls/register.html'
    success_url = reverse_lazy('polls:login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('polls:mainPage')


class LoginUser(LoginView):
    form_class = AuthenticationForm
    template_name = 'polls/login.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        return reverse_lazy('polls:mainPage')

def logout_user(request):
    logout(request)
    return redirect('polls:mainPage')


