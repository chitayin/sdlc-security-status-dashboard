from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            extra_context={
                "demo_email": settings.DEMO_USER_EMAIL,
                "demo_password": settings.DEMO_USER_PASSWORD,
            }
        ),
        name="login"
    ),

    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(),
        name="logout"
    ),

    path("", include("apps.telemetry.urls")),
]