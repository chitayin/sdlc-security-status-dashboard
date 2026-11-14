from django.urls import path
from . import views

# Explicit namespace to prevent collisions across potential future apps
app_name = 'telemetry'

urlpatterns = [
    # Main system landing layout (DashboardController)
    path('', views.dashboard_controller, name='dashboard'),
    
    # Real-time data pipeline endpoint (AnalyticsEngine)
    path('analytics/engine/', views.analytics_engine, name='analytics_engine'),
]
