from django.contrib import admin
from .models import Forum, Topic, Message, Program
# Register your models here.

admin.site.register(Forum)
admin.site.register(Topic)
admin.site.register(Message)
admin.site.register(Program)