    # -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path
from django.conf.urls import include
from .views import login_view, register_user, logout_user
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('logout_user/', logout_user, name="logout_user"),
    # path('auth/', include('social_django.urls', namespace='social')),  # <- Here
]