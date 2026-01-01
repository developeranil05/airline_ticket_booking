from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import logout
from django.shortcuts import redirect
from bookings.template_views import register_view
from bookings.auth_views import CustomLoginView

def logout_view(request):
    logout(request)
    return redirect('/')

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", CustomLoginView.as_view(), name='login'),
    path("accounts/register/", register_view, name='register'),
    path("accounts/logout/", logout_view, name='logout'),
    path("", include("bookings.urls")),
]
