from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .models import Forum, Topic, Message, Program
from .forms import ForumForm

# Create your views here.

def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        
        try:
            user = User.object.get(username=username)
        except:
            messages.error(request, 'User does not exist')
            
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username or Password does not exist')
            
    context = {'page':page}
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerUser(request):
    form = UserCreationForm()
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error has occured during registration of your account.')
            
    return render(request, 'base/login_register.html', {'form':form})

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    forums = Forum.objects.filter(
        Q(topic__name__icontains=q) | 
        Q(name__icontains=q) | 
        Q(description__icontains=q)
    )
    
    topics = Topic.objects.all()
    programs = Program.objects.all()
    activity_messages = Message.objects.all().filter(Q(forum__topic__name__icontains=q))
    
    context = {'forums':forums, 'topics':topics, 'programs':programs, 'activity_messages':activity_messages}
    return render(request, 'base/home.html', context)

def forum(request, pk):
    forum = Forum.objects.get(id=pk)
    forum_messages = forum.message_set.all()
    participants = forum.participants.all()
    
    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            forum = forum,
            body = request.POST.get('body')
        )
        forum.participants.add(request.user)
        return redirect('forum', pk=forum.id)
    
    context = {'forum':forum, 'forum_messages':forum_messages, 'participants':participants}        
    return render(request, 'base/forum.html', context)

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    forums = user.forum_set.all()
    activity_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user':user, 'forums':forums, 'activity_messages':activity_messages, 'topics':topics}
    return render(request, 'base/profile.html', context)

def programPage(request, pk):
    program = Program.objects.get(id=pk)
    program_title = program.name
    program_body = program.body
    #program_topic = program.topic
    #rel_forum = Forum.objects.filter(
    #    Q(topic__name__icontains=program_topic.name)
    #).first()
    
    
    context = {'program':program, 'program_title':program_title, 'program_body':program_body}
    return render(request, 'base/program.html', context)

@login_required(login_url='login')
def createForum(request):
    form = ForumForm()
    
    if request.method == 'POST':
        form = ForumForm(request.POST)
        if form.is_valid():
            forum = form.save(commit=False)
            forum.host = request.user
            forum.save()
            return redirect('home')
    
    context = {'form':form}
    return render(request, 'base/forum_form.html', context)