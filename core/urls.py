from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('register-child/', views.register_redirect, name='register_child'),

    # Parent Dashboard & Child Profile Management (Task 08)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/child/add/', views.child_add, name='child_add'),
    path('dashboard/child/<int:child_id>/', views.child_detail, name='child_detail'),
    path('dashboard/child/<int:child_id>/edit/', views.child_edit, name='child_edit'),
    path('dashboard/child/<int:child_id>/delete/', views.child_delete, name='child_delete'),
]
