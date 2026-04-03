from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    path('login_view/', views.login_view, name='login_view'),
    path('signup_view/', views.signup_view, name='signup_view'),
    path('reset_view/', views.reset_view, name='reset_view'),
    path('confirm-reset/<str:email>', views.reset_confirm, name='reset_confirm'),
    path('timetable-results/', views.timetable_grid_view, name='timetable_results'), 
    path('run-engine/', views.run_timetable_engine, name='run_timetable_engine'),
    path('timetable-grid/', views.timetable_grid_view, name='timetable_grid'),
    
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('generate/', views.generate, name='generate'),
    path("upload-data/", views.upload_data_view, name="upload_data"),
    path('download-template/', views.download_template, name='download_template'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/contact/', views.update_contact, name='update_contact'),
    path('profile/password/', views.change_password, name='change_password'),
]