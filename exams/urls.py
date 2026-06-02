from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('exam/', views.exam_view, name='exam'),
    path('api/save-answer/', views.save_answer_api, name='save_answer_api'),
    path('api/submit-exam/', views.submit_exam_api, name='submit_exam_api'),
    path('result/', views.result_view, name='result'),
]