from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('register/', views.registerUser, name='register'),
    
    path('', views.home, name="home"),
    path('forum/<str:pk>/', views.forum, name="forum"),
    path('profile/<str:pk>', views.userProfile, name='user-profile'),
    path('program/<str:pk>/', views.programPage, name="program"),
    
    path('create-forum/', views.createForum, name="create-forum"),
    ]