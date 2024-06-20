from django.forms import ModelForm
from survey.models import *
from django import forms
from django.forms.models import inlineformset_factory
from django.forms import widgets
from application_master.models import MasterLookUp
from django.conf import settings
# import bleach

class QuestionForm(forms.ModelForm):
    master_question = forms.ModelChoiceField(queryset=MasterLookUp.objects.filter(parent=None), required=False, widget=forms.Select(attrs={'class': 'col-sm-12 form-control', 'data-style': 'select-with-transition'}))
    class Meta:
        model=Question
        widgets = {
              'qtype': forms.Select(attrs={'class': 'col-sm-12 form-select', 'data-style': 'select-with-transition'}),
              'api_qtype': forms.Select(attrs={'class': 'col-sm-12 form-select', 'data-style': 'select-with-transition'}),
              'api_json': forms.Textarea(attrs={'rows': 5, 'cols': 30}),
              'question_filter': forms.Select(attrs={'class':'col-sm-12 form-select', 'data-style': 'select-with-transition'}),
          }
        fields=['qtype', 'text', 'code', 'mandatory', 'master_question', 'api_qtype', 'api_json','question_filter']

    # def clean_text(self):
    #     name = self.cleaned_data.get('text', '')
    #     cleaned_text = bleach.clean(name, settings.BLEACH_VALID_TAGS, settings.BLEACH_VALID_ATTRS, settings.BLEACH_VALID_STYLES)
    #     return cleaned_text


class ChoiceForm(forms.ModelForm):
    class Meta:
        model=Choice
        widgets = {
            'text': forms.TextInput(attrs={'class': 'col-sm-12 form-control'} ),
            'code': forms.NumberInput(attrs={'class': 'col-sm-12 form-control'} ),
            'uuid': forms.TextInput(attrs={'class': 'col-sm-12 form-control'} ),
        }
        fields=['text', 'code','uuid']

    # def clean_text(self):
    #     name = self.cleaned_data.get('text', '')
    #     cleaned_text = bleach.clean(name, settings.BLEACH_VALID_TAGS, settings.BLEACH_VALID_ATTRS, settings.BLEACH_VALID_STYLES)
    #     return cleaned_text