# Model managers for survey models
from django.db import models
# Import prerequisites



class ActiveQuerySet(models.QuerySet):

    def get_or_none(self, *args, **kwargs):
        # Returns object and return none if it's not present
        try:
            return self.get(*args, **kwargs)
        except self.model.DoesNotExist:
            return None

    def export(self, fields=None):
        import csv
        if not fields:
            fields = [i.name
                      for i in self.model._meta.fields]
        file_name = '/tmp/%s.csv' % (str(self.model).replace('.', '_'))
        file_obj = open(file_name, 'w+')
        writer_obj = csv.writer(file_obj)
        writer_obj.writerow(fields)
        for i in self:
            writer_obj.writerow([getattr(i, j) for j in fields])
        file_obj.close()