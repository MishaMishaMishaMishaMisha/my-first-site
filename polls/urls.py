from django.urls import path
from . import views

app_name = 'polls'
# список урл-привязок
urlpatterns = [
    path('', views.mainPage, name='mainPage'),
    path('<int:dashboard_id>/', views.index, name='index'),
    path('createDashboard/', views.createDashboard, name='createDashboard'),
    path('find_dashboard/', views.find_dashboard, name='find_dashboard'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.RegisterUser.as_view(), name='register')
]