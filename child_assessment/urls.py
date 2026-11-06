"""
URL configuration for child_assessment project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('assessment/', include('assessment.urls')),
    path('results/', include('results.urls')),
]
