from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    path('', views.overview, name='overview'),
    path('assessment/<int:assessment_id>/', views.assessment_report, name='assessment_report'),
    path('<int:result_id>/', views.result_detail, name='detail'),
]
