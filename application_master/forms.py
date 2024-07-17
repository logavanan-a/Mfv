from django import forms
from . models import *
from django.utils.translation import gettext_lazy as _
import re
from django.core.validators import RegexValidator


class StateForm(forms.ModelForm):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'pattern':'[A-Za-z ]+','placeholder': 'Enter State Name '}),
        error_messages={'unique': _('This name already exists. Please enter a different name.')})
    
    class Meta:
        model = State
        fields = ['name'] 
    
class DistrictForm(forms.ModelForm):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'pattern':'[A-Za-z ]+','placeholder': 'Enter District Name '}),max_length=150)
    state = forms.ModelChoiceField(queryset=State.objects.filter(active=2).order_by("name"),required = True,empty_label="Select State")

    def __init__(self, *args, **kwargs):
        super(DistrictForm, self).__init__(*args, **kwargs)
        self.fields['state'].widget.attrs['class'] = 'form-select select2'

    class Meta:
        model=District
        fields=['state', 'name']


class ProjectDonorMappingForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset=State.objects.filter(active=2).order_by("name"),required = True,empty_label="Select State")
    donor = forms.ModelChoiceField(queryset=State.objects.filter(active=2).order_by("name"),required = True,empty_label="Select State")

    def __init__(self, *args, **kwargs):
        super(ProjectDonorMappingForm, self).__init__(*args, **kwargs)
        self.fields['project'].widget.attrs['class'] = 'form-select select2'
        self.fields['donor'].widget.attrs['class'] = 'form-select select2'

    class Meta:
        model=ProjectDonorMapping
        fields=['project', 'donor']

class PartnerForm(forms.ModelForm):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter Name'}), max_length=150, strip=True)
    # partner_logo = forms.FileField(required=False)

    class Meta:
        model = Partner
        fields = ['name']

    def save(self, commit=True):
        instance = super(PartnerForm, self).save(commit=False)  
        instance.slug = self.cleaned_data['name'].lower() 
        if commit:
            instance.save()
        return instance

class MissionForm(forms.ModelForm):
    MISSION_CHOICES = ((1,'Indicator'),(2,'Form'))
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter Name'}), max_length=150, strip=True)
    short_description = forms.CharField(widget=forms.Textarea(attrs={'placeholder':'Enter short description','rows':4}),required = False)
    mission_template = forms.ChoiceField(choices=MISSION_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-select'}), initial=1)
    age_group_option = forms.IntegerField(required=True,  initial=1)

    def __init__(self, *args, **kwargs):
        super(MissionForm, self).__init__(*args, **kwargs)            
        self.fields['short_description'].widget.attrs['class'] = 'form-control'

    class Meta:
        model = Mission
        fields = ['name', 'mission_template','slug','age_group_option' , 'short_description']

    def save(self, commit=True):
        instance = super(MissionForm, self).save(commit=False)  
        instance.slug = self.cleaned_data['name'].lower() 
        if commit:
            instance.save()
        return instance


class ProjectForm(forms.ModelForm):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter Name'}), max_length=150, strip=True)
    partner_mission_mapping = forms.ModelChoiceField(queryset=PartnerMissionMapping.objects.filter(active=2),required = True,empty_label="Select Partnermissionmapping")
    state = forms.ModelChoiceField(queryset=State.objects.filter(active=2).order_by("name"),required = True,empty_label="Select State")
    district = forms.ModelChoiceField(queryset=District.objects.filter(active=2).order_by("name"),required = True,empty_label="Select District")
    location = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter location'}), max_length=150)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    donor = forms.ModelChoiceField(queryset=Donor.objects.all(), required=True, empty_label="Select Donor")
    additional_info = forms.CharField(widget=forms.Textarea(attrs={'placeholder':'Enter description','rows':3}),required = False)

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')  
        super(ProjectForm, self).__init__(*args, **kwargs)
        if instance:  
            try:
                donor_mapping = ProjectDonorMapping.objects.get(project=instance)
                self.initial['donor'] = donor_mapping.donor.id  
            except ProjectDonorMapping.DoesNotExist:
                pass

        self.fields['partner_mission_mapping'].widget.attrs['class'] = 'form-select select2'
        self.fields['state'].widget.attrs['class'] = 'form-select select2'
        self.fields['district'].widget.attrs['class'] = 'form-select select2'
        self.fields['donor'].widget.attrs['class'] = 'form-select select2'
        self.fields['additional_info'].widget.attrs['class'] = 'form-control'

        if self.instance.pk:
            if self.instance.district.state:
                self.fields['district'].queryset = self.fields['district'].queryset.filter(state_id=self.instance.district.state.id)
            self.fields['state'].initial = self.instance.district.state

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', 'End date must be later than start date.')

        return cleaned_data
            
    class Meta:
        model = Project
        fields = ['name', 'partner_mission_mapping', 'state', 'district','location','start_date','end_date', 'donor', 'additional_info']


class DonorForm(forms.ModelForm):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter Name'}), max_length=150, strip=True)
    # logo = forms.FileField(required=False)
    
    class Meta:
        model = Donor
        fields = ['name']

class MissionindicatorcategoryForm(forms.ModelForm):
    CATEGORY_CHOICES = ((1,'Programme Indicator'),
                        (2,'Finance Indicator'))
    VC_CHOICES = list(CATEGORY_CHOICES)
    VC_CHOICES.insert(0, ("", "Select Vision Center Type"))

    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter Name'}), max_length=150, strip=True)
    mission = forms.ModelChoiceField(queryset=Mission.objects.filter(active=2),required = True,empty_label="Select mission")
    category_type = forms.ChoiceField(choices=VC_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-select'}))
    label_configuration = forms.IntegerField(required=True, initial=1)
    
    def __init__(self, *args, **kwargs):
        super(MissionindicatorcategoryForm, self).__init__(*args, **kwargs)
        self.fields['mission'].widget.attrs['class'] = 'form-select select2'

    class Meta:
        model = MissionIndicatorCategory
        fields = ['name', 'mission', 'category_type', 'label_configuration']


class MissionindicatorForm(forms.ModelForm):
    IT_CHOICES = ((1,'Gender Base'),
                  (2,'Total'),
                  (3,'Actuals'),
                  (4,'Actuals With Grants Received'))
    IT_CHOICES = list(IT_CHOICES)
    IT_CHOICES.insert(0, ("", "Select Vision Center Type"))

    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter Name'}), max_length=150, strip=True)
    category = forms.ModelChoiceField(queryset=MissionIndicatorCategory.objects.filter(active=2),required = True,empty_label="Select mission indicator category")
    indicator_type = forms.ChoiceField(choices=IT_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-select'}))
    
    def __init__(self, *args, **kwargs):
        super(MissionindicatorForm, self).__init__(*args, **kwargs)
        self.fields['category'].widget.attrs['class'] = 'form-select select2'

    class Meta:
        model = MissionIndicator
        fields = ['name', 'category', 'indicator_type']


