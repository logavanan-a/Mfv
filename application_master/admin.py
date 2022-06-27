from django.contrib import admin
from .models import *

admin.site.register(State)
admin.site.register(District)
admin.site.register(Partner)
admin.site.register(Mission)
admin.site.register(PartnerMissionMapping)
admin.site.register(Donor)

