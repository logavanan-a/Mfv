from django.contrib import admin
from .models import *

# Register your models here.

# admin.site.register(MailTemplate)
admin.site.register(MailData)

@admin.register(MailTemplate)
class MailTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_name','description','subject','content','created','html_template']
    # fields = ['created','template_name','description','subject','content','html_template']
    # list_filter = ('created_by',)

    # def is_active(self, obj):
    #     return obj.active == 2 
    # is_active.boolean = True

# @admin.register(MailData)
# class MailDataeAdmin(admin.ModelAdmin):
#     list_display = ['template_name','subject','content','created']
#     fields = ['created','template_name','subject','content']
#     # list_filter = ('created_by',)

#     def is_active(self, obj):
#         return obj.active == 2 
#     is_active.boolean = True