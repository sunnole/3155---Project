#import os
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .models import Forum, Topic, Message, Program, Chat
from .forms import ForumForm
from .webScraper import parse_page, fetch_page, extract_name
from django.contrib.admin.views.decorators import staff_member_required
# import httpx
# from asgiref.sync import sync_to_async
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator
# from bs4 import BeautifulSoup
# import requests
# from numpy.distutils.lib2def import output_def
# from django.http import HttpResponse

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

# Render of Forum and Reply system
def forum(request, pk):
    forum = Forum.objects.get(id=pk)
    forum_messages = forum.message_set.filter(parent_message__isnull=True)
    participants = forum.participants.all()
    
    if request.method == 'POST':
        parent_message_id = request.POST.get('parent_message_id')
        parent_message = Message.objects.get(id=parent_message_id) if parent_message_id else None
        message = Message.objects.create(
            user = request.user,
            forum = forum,
            body = request.POST.get('body'),
            parent_message = parent_message
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
    program = get_object_or_404(Program, pk=pk)
    return render(request, 'base/program.html', {'program': program})

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

# Web Scraper
@staff_member_required
def scrapePage(request):
    context = {"message": None, "program": None}

    if request.method == 'POST':
        url = request.POST.get('url')

        # Validate URL (For UNCC webpages only)
        if not url or not re.match(r'^https://[a-zA-Z-]+\.charlotte\.edu', url):
            context["message"] = "Invalid URL. Please enter valid UNCC URL."
            return render(request, "base/scraper_form.html", context)

        try:
            # Fetch page
            html_content = fetch_page(url)

            # Extract name and parse
            program_name = extract_name(html_content)
            parsed_program = parse_page(html_content)

            # Convert parsed data to database suitable format
            body_content = ""
            for section in parsed_program:
                tag = section.get("tag", "")
                content = section.get("content", "")

                if tag == 'ul' or tag == 'ol':  # If it's a list
                    body_content += f"<{tag}>"
                    for list_item in content.splitlines():  # Split by new lines for each list item
                        body_content += f"<li>{list_item}</li>"  # Convert list item to HTML list item
                    body_content += f"</{tag}>"
                elif tag == 'p':  # If it's a paragraph
                    body_content += f"<p>{content}</p>"  # Wrap paragraph content in <p> tags
                elif tag in ['h1', 'h2', 'h3', 'h4']:  # For headers
                    body_content += f"<{tag}>{content}</{tag}>"  # Add HTML headers like <h2>, <h3>, etc.

            # Save converted data to database
            topic, _ = Topic.objects.get_or_create(name="Graduate Programs")
            program, created = Program.objects.update_or_create(name=program_name, topic=topic, defaults={"body": body_content})

            # Messages
            if created:
                context["message"] = f"Program '{program_name}' has been created."
            else:
                context["message"] = f"Program '{program_name}' has been updated."
            context["program"] = program

        except Exception as e:
            # return JsonResponse({"success": False, "message": f"An error occurred: {str(e)}"}, status=500)
            context["message"] = f"An error has occurred during program creation: {e}"

        return render(request, "base/scraper_form.html", context)

    elif request.method == 'GET':
        return render(request, "base/scraper_form.html", context)

# Send private message
# @login_required(login_url='login')
# def send_pm(request, recipient_id):
#     recipient = User.objects.get(id=recipient_id)
#
#     if request.method == 'POST':
#         body = request.POST.get('body')
#         Chat.objects.create(sender=request.user, recipient=recipient, body=body)
#         return redirect('user-profile', pk=recipient.id)
#
#     context = {'recipient':recipient}
#     return render(request, 'base/send_pm.html', context)
#
# # User chat history
# @login_required(login_url='login')
# def user_chats(request):
#     received_messages = Chat.objects.filter(recipient=request.user)
#     sent_messages = Chat.objects.filter(sender=request.user)
#
#     conversations = []
#
#     for message in sent_messages:
#         other_user = message.recipient
#         if not any(conv['user'] == other_user for conv in conversations):
#             # Get all messages with this user
#             messages_with_user = sent_messages.filter(recipient=other_user) | received_messages.filter(sender=other_user)
#             messages_with_user = messages_with_user.order_by('created_at')
#             conversations.append({'user': other_user, 'messages': messages_with_user})
#
#     for message in received_messages:
#         other_user = message.sender
#         if not any(conv['user'] == other_user for conv in conversations):
#             messages_with_user = sent_messages.filter(recipient=other_user) | received_messages.filter(
#                 sender=other_user)
#             messages_with_user = messages_with_user.order_by('created_at')
#             conversations.append({'user': other_user, 'messages': messages_with_user})
#
#     context = {'conversations':conversations}
#     return render(request, 'base/user_chats.html', context)
