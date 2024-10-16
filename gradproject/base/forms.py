from django.forms import ModelForm
from .models import Forum

class ForumForm(ModelForm):
    class Meta:
        model = Forum
        fields = '__all__'
        exclude = ['host', 'participants']