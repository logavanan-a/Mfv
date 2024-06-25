from rest_framework import serializers
from .models import *
import pytz


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