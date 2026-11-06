from django.urls import path
from . import views

app_name = 'assessment'

urlpatterns = [
    # Information & Guides
    path('', views.overview, name='overview'),
    path('aptitude/', views.aptitude_intro, name='aptitude_intro'),
    path('interest/', views.interest_intro, name='interest_intro'),

    # Child Intake & Track Selection
    path('register/', views.child_register, name='register'),
    path('start/', views.child_register, name='start'),
    path('select/<int:child_id>/', views.assessment_selection, name='selection'),
    path('initiate/<int:child_id>/<str:assessment_type>/', views.initiate_assessment, name='initiate_assessment'),

    # Questionnaire Engine
    path('<int:assessment_id>/take/', views.questionnaire_entry, name='take'),
    path('<int:assessment_id>/question/<int:question_index>/', views.questionnaire_question, name='question'),
    path('<int:assessment_id>/complete/', views.assessment_completion, name='completion'),
]
