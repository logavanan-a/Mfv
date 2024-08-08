from rest_framework import serializers
from .models import *
import pytz
from dashboard.models import MonthlyDashboard,Remarks

class LabelLanguageTranslationSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source='applabel.name')
    l_id = serializers.IntegerField(source='language.id')

    class Meta:
        model = LabelLanguageTranslation
        fields = ['id','label' ,'text', 'l_id' , 'modified']

    def to_representation(self, instance):
        # Customize the representation here
        representation = super().to_representation(instance)
        # Convert the 'modified' field to a datetime object
        modified_datetime = datetime.strptime(representation['modified'], '%Y-%m-%dT%H:%M:%S.%f%z')
        # Add additional fields or modify existing ones
        representation['modified'] = modified_datetime.astimezone(pytz.timezone('Asia/Kolkata')).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S.%f')
        # handle null value in parent fields
        # representation['parent'] = 0 if representation['parent'] is None else representation['parent']
        return representation
    

class LinkageListingSerializer(serializers.Serializer):
    modified_on = serializers.CharField(required=False)    


class CommaSeparatedListField(serializers.Field):
    """
    A custom serializer field to handle comma-separated string to list conversion.
    """

    def to_representation(self, value):
        # Convert list to string for representation
        if isinstance(value, list):
            return ','.join(value)
        return value

    def to_internal_value(self, data):
        # Convert comma-separated string to list
        if isinstance(data, str):
            return [item.strip() for item in data.split(',')]
        return data
        
class MonthlyDashboardSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S.%f',required=False)
    modified = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S.%f',required=False)
    children_covered_uuid =  CommaSeparatedListField()
    school_covered_uuid =  CommaSeparatedListField()
    teachers_train_uuid =  CommaSeparatedListField()
    children_pres_uuid =  CommaSeparatedListField()
    child_prov_spec_uuid =  CommaSeparatedListField()
    pgp_uuid =  CommaSeparatedListField()
    children_reffered_uuid =  CommaSeparatedListField()
    child_prov_hos_uuid =  CommaSeparatedListField()
    children_adv_uuid =  CommaSeparatedListField()
    children_prov_sgy_uuid =  CommaSeparatedListField()
    swc_uuid =  CommaSeparatedListField()
    # partner = serializers.SerializerMethodField()
    uuid = serializers.CharField(source='creation_key') 
    approved_status = serializers.IntegerField(source='current_status') 
    # creation_key = serializers.CharField(required=False)
    # submitted_by = serializers.SerializerMethodField()

    class Meta:
        model = MonthlyDashboard
        exclude = ['creation_key','partner','submitted_by','current_status']

    def create(self, validated_data):
        partner = self.context.get('partner')
        submitted_by = self.context.get('submitted_by')
        validated_data['partner_id'] = partner
        validated_data['submitted_by_id'] = submitted_by
        return MonthlyDashboard.objects.create(**validated_data)

class RemarksSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(source='created',format='%Y-%m-%d %H:%M:%S.%f')
    modified_at = serializers.DateTimeField(source='modified',format='%Y-%m-%d %H:%M:%S.%f')
    response_id = serializers.CharField(source='content_object.creation_key') 
    remark_uuid = serializers.CharField(source='content_object.creation_key') 
    created_by = serializers.CharField(source='content_object.submitted_by.username') 

    class Meta:
        model = Remarks
        exclude = ['created','modified','listing_order','object_id','user','content_type']

