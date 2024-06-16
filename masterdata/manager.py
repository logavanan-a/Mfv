from django.db import models
# Model managers for masterdate models


class ActiveQuerySet(models.QuerySet):

    def custom_values(self,*args,**kwargs):
        #Custom values function for dynamic lisitng
        model_fields = self.model._meta.get_fields()
        model = [str(i.name) for i in model_fields]
        json_fields = []
        json_fields = [str(i.name) for i in model_fields if i.__class__.__name__ == 'JSONField']
        other_model_fields = [{i[0].name:i[0].model} for i in self.model._meta.get_fields_with_model()]
        responses = []
        for one in self:
            one_value = {}
            for i in args[0]:
                one_value.update(self.get_from_model_or_jsonfield(model,json_fields,one,i))
            responses.append(one_value)
        return responses

    def get_from_model_or_jsonfield(self,model,json_fields,one,i):
        one_value = {}
        if i in model:
            try:
                one_value[i]=str(getattr(one,i))
            except:
                one_value[i]=getattr(one,i)
        else:
            one_value.update(self.search_in_jsonfield(json_fields,one,i))
        return one_value

    def search_in_jsonfield(self,json_fields,one,i):
        one_value = {}
        for jf in json_fields:
            try:
                json_value = eval(getattr(one,jf))
            except:
                json_value = getattr(one,jf)
            if type(json_value) == list:
                json_value = json_value[0]
            json_keys = json_value.keys()
            if i in json_keys:
                one_value[i] = json_value[i]
                if type(json_value[i]) == list:
                    one_value[i] = json_value[i]
        return one_value

    def active_items(self):
        # Returns active items only
        return self.filter(active=2)

    def get_or_none(self, *args, **kwargs):
        # Returns object and return none if it's not present
        try:
            return self.get(*args, **kwargs)
        except self.model.DoesNotExist:
            return None

    def filter_if(self, *args, **kwargs):
        for i in [i for i in kwargs if not kwargs.get(i)]:
            kwargs.pop(i)
        return super(ActiveQuerySet, self).filter(*args, **kwargs)

    def one(self, *args, **kwargs):
        # Returns one of the objects
        # Usefull while using shell
        return self.filter(*args, **kwargs).order_by('pk')[0]

    def __repr__(self):
        # Makes it easy to distinguish between qs and list
        return "#%s#" % (super(ActiveQuerySet, self).__repr__())

    def ids(self):
        # returns list of ids
        return [i.id for i in self]
        
#    def get_section(self):
#        

    def vals(self, key, tipe={}):
        if tipe == {}:
            return set(self.values_list(key, flat=True))
        elif tipe == []:
            return self.values_list(key, flat=True)

    def each(self, save=False, func=None):
        if hasattr(save, '__call__'):
            func = save
            save = False
        for obj in self:
            func(obj)
            if save:
                obj.save()

    def sigma(self, attr):
        return self.aggregate(x=models.Sum(attr))['x'] or 0

    def draw(self, fields=None, display=30):
        from texttable import Texttable
        display = min(display, self.count())
        if not fields:
            fields = [i.name
                      for i in self.model._meta.fields
                      if i.name not in ['created', 'modified']]
        t = Texttable()
        t.add_rows([fields] + [
            [getattr(i, j) for j in fields]
            for i in self[:display]
        ])
        return "\nDisplaying {no} of {total} {model}s\n".format(
            no=display, total=self.count(), model=self.model.__name__
        ) + '-' * 40 + '\n' + t.draw()

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
        
    def latest_one(self, *args, **kwargs):
        # Returns one of the objects
        # Usefull while using shell
        try:
            return self.filter(*args, **kwargs).order_by('-id')[0]
        except:
            return None
