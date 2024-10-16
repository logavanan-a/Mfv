from rest_framework import serializers
from .models import Mission, Project, ProjectDonorMapping

class LoginAndroidSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True, allow_blank=False, max_length=100)
    password = serializers.CharField(
        required=True, allow_blank=False, max_length=100)


# Serializer for Donor Details
class DonorSerializer(serializers.ModelSerializer):
    donor_name = serializers.CharField(source='donor.name')
    id = serializers.IntegerField(source='donor_id')
    class Meta:
        model = ProjectDonorMapping
        fields = ('id', 'donor_name')

# Serializer for Project
class ProjectSerializer(serializers.ModelSerializer):
    donor_details = serializers.SerializerMethodField()
    project_name = serializers.CharField(source='name')
    project_id = serializers.IntegerField(source='id')
    order = serializers.IntegerField(source='id')
    location = serializers.IntegerField(source='district_id')
    created_on = serializers.DateTimeField(source='created',format='%Y-%m-%d %H:%M:%S.%f')

    class Meta:
        model = Project
        fields = ['project_name', 'project_id', 'created_on', 'location', 'order', 'donor_details']

    def get_donor_details(self, obj):
        # Get the related donor mappings for this project
        donors = ProjectDonorMapping.objects.filter(active=2,project=obj)
        return DonorSerializer(donors, many=True).data

# Serializer for Mission
class MissionSerializer(serializers.ModelSerializer):
    project_list = serializers.SerializerMethodField()
    mission_id = serializers.IntegerField(source='id')
    mission_name = serializers.CharField(source='name')
    order = serializers.IntegerField(source='id')

    class Meta:
        model = Mission
        fields = ['mission_id', 'mission_name', 'order', 'project_list']

    def get_project_list(self, obj):
        user_projects = self.context.get('user_projects')

        # Get the related projects for this mission
        projects = Project.objects.filter(partner_mission_mapping__mission = obj,id__in=user_projects,active=2)
        return ProjectSerializer(projects, many=True).data
