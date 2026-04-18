from django.urls import path
from . import views

urlpatterns = [
    path('',            views.login_view,     name='login'),
    path('logout/',     views.logout_view,    name='logout'),
    path('domain/',     views.domain_view,    name='domain'),
    path('profile/',    views.profile_view,   name='profile'),
    path('interview/',  views.interview_view, name='interview'),
    path('complete/',   views.complete_view,  name='complete'),
    path('api/evaluate/', views.evaluate_api, name='evaluate_api'),
]
