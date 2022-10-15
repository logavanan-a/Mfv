# from django.db import models
# from master_data.models import BaseContent

# # Create your models here.
# from django.core.validators import RegexValidator

# alphanumeric = RegexValidator(
#     r'^[0-9a-zA-Z-]*$', 'Only alphanumeric characters are allowed.')


# class ReportMeta(BaseContent):
#     report_slug = models.CharField(
#         max_length=500, blank=True, null=True, validators=[alphanumeric])
#     report_title = models.CharField(max_length=500, blank=True, null=True)
#     report_header = models.JSONField(
#         blank=True, null=True, help_text="report headers in json format")
#     report_query = models.JSONField(
#         blank=True, null=True, help_text="sql query and related filter details as json - with keys sqlquery, filters and etc")
#     display_order = models.IntegerField(
#         blank=True, null=True, help_text="order in which the charts have to be displayed")
#     filter_info = models.JSONField(
#         blank=True, null=True, help_text="report filters meta data in json format")
#     sort_info = models.JSONField(
#         blank=True, null=True, help_text="report sort meta data in json format")

#     class Meta:
#         verbose_name_plural = "Report Meta"

#     def __str__(self):
#         return self.report_slug

from django.db import models
from application_master.models import BaseContent

# Create your models here.
from django.core.validators import RegexValidator

alphanumeric = RegexValidator(
    r'^[0-9a-zA-Z-]*$', 'Only alphanumeric characters are allowed.')


class ReportMeta(BaseContent):
    page_slug = models.CharField(
        max_length=500, blank=True, null=True, validators=[alphanumeric])
    report_slug = models.CharField(
        max_length=500, blank=True, null=True, validators=[alphanumeric], unique=True)
    report_title = models.CharField(max_length=500, blank=True, null=True)
    report_header = models.JSONField(
        blank=True, null=True, help_text="report headers in json format")
    report_query = models.JSONField(
        blank=True, null=True, help_text="sql query and related filter details as json - with keys sqlquery, filters and etc")
    display_order = models.IntegerField(
        blank=True, null=True, help_text="order in which the charts have to be displayed")
    filter_info = models.JSONField(
        blank=True, null=True, help_text="report filters meta data in json format")
    sort_info = models.JSONField(
        blank=True, null=True, help_text="report sort meta data in json format")
    custom_export_header = models.JSONField(
        blank=True, null=True, help_text="custom headers for excel export to handle multilevel headers in json format")

    class Meta:
        verbose_name_plural = "Report Meta"
        ordering = ['display_order']

    def __str__(self):
        return self.report_slug
