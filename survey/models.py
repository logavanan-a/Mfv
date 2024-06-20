from ast import literal_eval
from datetime import datetime, timedelta
from application_master.models import *
# from common_methods import *
# from userroles.models import UserRoles
from django.db import models
# from constants import OPTIONAL
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, pre_save
from django.forms.models import model_to_dict
from django.core.cache import cache
from django.core.signals import got_request_exception
from uuid import uuid4
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import JSONField
# from Convene2.settings import CACHES
# from Convene2.settings import INSTANCE_CACHE_PREFIX


# from userroles.serializers import user_setup


VALIDATION_TYPE = (('R', 'Required'), ('O', 'Optional'),)
DISPLAY_TYPE_CHOICES = (('0', 'Web'), ('1', 'Android'),('2','Report'),('3','SearchFilter'))
PERIODICITY_CHOICES = (
        (0, '---NA---'), (1, 'Daily'), (2, 'Weekly'),
        (3, 'Monthly'), (4, 'Quarterly'), (5, 'Half Yearly'),
        (6, 'Yearly'),(7,'Onetime activity'))
SURVEY_TYPE_CHOICES = (
        (0, 'OneTime Activity'), (1, 'Extended activity')
    )
CAPTURE_LEVEL_CHOICES = ((1,'Web'),(2,'App'),(3,'Both'))
SURVEY_DEACTIVATE_REASON = (("Program Discontinued","Program Discontinued"), ("Program Major Revamp","Program Major Revamp"), ("Others","Others"))
DEACTIVATE_REASONS = ((1, 'User Transfered'), (2, 'Shutdown'),)

## DataEntryLevel models
class DataEntryLevel(BaseContent):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)

    def __str__(self):
        # sets name as unicode
        return self.name

    def save(self, *args, **kwargs):
        # Customise save method
        self.slug = slugify('%s' % (
            self.name))
        super(DataEntryLevel, self).save(*args, **kwargs)




class Survey(BaseContent):
    #                                                     survey
    # tagging datacentre through survey
    # eg: Daily based survey or weekly based survey
    DISPLAY_CHOICES = (('single', 'single'), ('multiple', 'multiple'))
    # Fields for survey
    name = models.CharField(max_length=100)
    survey_type = models.IntegerField(choices=SURVEY_TYPE_CHOICES, default=0)
    data_entry_level = models.ForeignKey(DataEntryLevel,
                                         blank=True, null=True,on_delete=models.DO_NOTHING)
    slug = models.SlugField(_('slug'), max_length=255, unique=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    survey_order = models.PositiveIntegerField(default=0, verbose_name=_("order"),)
    display_type = models.CharField(
        default='multiple', choices=DISPLAY_CHOICES, max_length=25)
    periodicity = models.IntegerField(
        'Periodicity',
        default=0, choices=PERIODICITY_CHOICES)
    expiry_age = models.PositiveIntegerField(default=0, blank=True, null=True)
    theme = models.ForeignKey(MasterLookUp,null=True,on_delete=models.DO_NOTHING)
    content_type = models.ForeignKey(ContentType, blank=True, null=True,on_delete=models.DO_NOTHING)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    config = models.JSONField(default=dict)
    extra_config = models.JSONField(default=dict)
    procedure_func = models.CharField(max_length=100,blank=True,null=True)
    surveyparent = models.ForeignKey('self', blank=True, null=True,related_name='Parent_Survey',on_delete=models.DO_NOTHING)
    categories = models.ForeignKey(MasterLookUp, related_name='Survey_Category',
                                           blank=True,null=True,on_delete=models.DO_NOTHING)
    capture_level_type = models.IntegerField(default=3, choices=CAPTURE_LEVEL_CHOICES)
    # this form entry level is to specify capturing data from app(1) or web(2) or both(3) of integer values 
    form_entry_level = models.PositiveIntegerField(default=1,blank=True, null=True)
    survey_module = models.PositiveIntegerField(default=0,blank=True, null=True)# this is to specify which the category like program module.Now value 1 is program module in swayam.later any modules are then we can use it with different values.Value 0 is default .It is normal survey
    report_generated = models.DateTimeField(blank=True, null=True)
    report_filename = models.CharField(max_length=2500,blank=True,null=True)
    deactivated_reason = models.CharField(max_length=500,blank=True,null=True,choices=SURVEY_DEACTIVATE_REASON)
    deactivated_date   = models.DateTimeField(blank=True, null=True)
    deactivated_user   = models.ForeignKey(User, blank=True, null=True,on_delete=models.DO_NOTHING)
    short_name = models.CharField(max_length=100,blank=True, null=True)

    def save(self, *args, **kwargs):
        # Customise save method
        if not self.slug:
            self.slug = slugify('%s-%s' % (
                self.name, str(uuid4().int)[:4]))
        super(Survey, self).save(*args, **kwargs)

    # #TODO: Not used in subhiksha application but used in apis not have any logic in subhiksha for rule engine
    # def get_survey_rule_engine(self):
    #     rule_engine_obj = None
    #     try:
    #         rule_engine_obj = RuleEngine.objects.get(content_type=ContentType.objects.get_for_model(self), object_id=self.id)
    #     except:
    #         pass
    #     return rule_engine_obj

    #TODO: Not used in subhiksha application but used in apis not have any logic in subhiksha for rule engine
#     def get_survey_rule_engine_for_surveylist(self,key):
#         survey_dict = {'0':'age_based_survey','1':'age_based_survey_or'}
#         key_value = survey_dict.get(str(key))
#         rule_engine_data = []
#         if self.get_survey_rule_engine() and self.get_survey_rule_engine().rule_engine.get(key_value):
# #            if self.get_survey_rule_engine().rule_engine.get(key_value):
#             for counter, rulesets in enumerate(self.get_survey_rule_engine().rule_engine.get(key_value)):
#                 if rulesets.get("type") == "age":
#                     age_question_id = rulesets.get("reference_question_id")
#                     try:
#                         split_text = rulesets.get("age").split('-')
#                         if split_text[1]:
#                             rule_engine_data.append({"data_type":"Number","operator":">=","question_id":str(age_question_id),"value": str(split_text[0])})
#                             rule_engine_data.append({"data_type":"Number","operator":"<=","question_id":str(age_question_id),"value": str(split_text[1])})
#                     except:
#                         pass
#                     try:
#                         split_text = rulesets.get("age").split('>')
#                         if split_text[1]:
#                             rule_engine_data.append({"data_type":"Number","operator":">","question_id":str(age_question_id),"value": str(split_text[1])})        
#                     except:
#                         split_text = rulesets.get("age").split('<')
#                         try:
#                             if split_text[1]:
#                                 rule_engine_data.append({"data_type":"Number","operator":"<","question_id":str(age_question_id),"value": str(split_text[1])})    
#                         except:
#                             pass 
#                 elif rulesets.get("type") == "value":
#                     age_question_id = rulesets.get("reference_question_id")
#                     value = rulesets.get("value")
#                     try:
#                         rule_engine_data.append({"data_type":"String","operator":"==","question_id":str(age_question_id),"value": str(value)})
#                     except:
#                         pass
#                 elif rulesets.get("type") == 'location':
#                     question_id = rulesets.get("reference_question_id")
#                     value = rulesets.get('value')
#                     level = rulesets.get('level')
#                     try:
#                         rule_engine_data.append({"data_type":"location","operator":"IN","question_id":str(question_id),"value": str(value),"level":int(level)})
#                     except:
#                         pass
#                 elif rulesets.get("type") == 'validate':
#                     question_id = rulesets.get("reference_question_id")
#                     value = rulesets.get("value")
#                     data_type = rulesets.get('data_type')
#                     operator = rulesets.get('operator')
#                     try:
#                         rule_engine_data.append({"data_type":data_type,"operator":operator,"question_id":str(question_id),"value": str(value)})
    #                 except:
    #                     pass                        
    #     return rule_engine_data

    # #TODO: Not used in subhiksha application but used in apis not have any logic in subhiksha for rule engine
    # def get_survey_rule_set(self):
    #     rule_engine_data_list = []
    #     if self.get_survey_rule_engine() and self.get_survey_rule_engine().rule_engine.get("age_based_display_questions"):
    #         for k, v in self.get_survey_rule_engine().rule_engine.get("age_based_display_questions").items():
    #             condition_list = v.keys()
    #             for condition in condition_list:
    #                 rule_engine_dict = {}
    #                 if v.get(condition).get("rulesets"):
    #                     rule_engine_data = []
    #                     # list(self.questions().exclude(id__in=v.get(condition).get("questions_to_display")).values_list("id", flat=True)) to send non display questions
    #                     # v.get(condition).get("questions_to_display") to send display questions
    #                     rule_engine_dict.update({"questions_to_display": v.get(condition).get("questions_to_display"),\
    #                                             "questions_not_to_display":list(self.questions().exclude(id__in=v.get(condition).get("questions_to_display")).values_list("id", flat=True))
    #                                             })
    #                     for counter, rulesets in enumerate(v.get(condition).get("rulesets")):
    #                         if rulesets.get("type") == "age":
    #                             age_question_id = rulesets.get("reference_question_id")
    #                             try:
    #                                 split_text = rulesets.get("age").split('-')
    #                                 if split_text[1]:
    #                                     rule_engine_data.append({"data_type":"Number","operator":">=","question_id":str(age_question_id),"value": str(split_text[0])})
    #                                     rule_engine_data.append({"data_type":"Number","operator":"<=","question_id":str(age_question_id),"value": str(split_text[1]),'is_base_form':rulesets.get('base_form',0)})
    #                             except:
    #                                 pass
    #                             try:
    #                                 split_text = rulesets.get("age").split('>')
    #                                 if split_text[1]:
    #                                     rule_engine_data.append({"data_type":"Number","operator":">","question_id":str(age_question_id),"value": str(split_text[1])})
    #                             except:
    #                                 pass
    #                         elif rulesets.get("type") == "value":
    #                             age_question_id = rulesets.get("reference_question_id")
    #                             value = rulesets.get("value")
    #                             try:
    #                                 rule_engine_data.append({"data_type":"String","operator":"==","question_id":str(age_question_id),"value": str(value),'is_base_form':rulesets.get('base_form',0)})
    #                             except:
    #                                 pass
    #                         elif rulesets.get('data_type') == 'location':
    #                             question_id = rulesets.get("reference_question_id")
    #                             value = rulesets.get("value")
    #                             data_type = rulesets.get('data_type')
    #                             level = rulesets.get('level')
    #                             operator = rulesets.get('operator')
    #                             rule_engine_data.append({"data_type":data_type,"operator":operator,"question_id":str(question_id),"value":value,"level":level,'is_base_form':rulesets.get('base_form',0)})
    #                         rule_engine_dict.update({"rulesets": rule_engine_data})
    #                 rule_engine_data_list.append(rule_engine_dict)
    #     return rule_engine_data_list

    # #TODO: Not used in anywhere
    # def get_text_skip_questions(self):
    #     return [str(quest.id) for quest in self.questions().filter(qtype='T') if quest.get_choices()]

    # #TODO: Not used in subhiksha application 
    # def get_text_skip_choices(self):
    #     question_choices = {}
    #     for quest in self.questions().filter(qtype='T'):
    #         choice_dict = {}
    #         if quest.get_choices():
    #             for choice in quest.get_choices():
    #                 range_list = str(choice.text)
    #                 choice_dict.update({str(choice.id): range_list})
    #             question_choices.update({str(quest.id): choice_dict})
    #     return question_choices

    #TODO: Not used in subhiksha application 
    # def get_survey_rule_engine_group_creation(self):
    #     create_group = None
    #     if self.get_survey_rule_engine():
    #         create_group = self.get_survey_rule_engine().rule_engine.get('create_new_beneficiary')
    #     return create_group

    # def get_survey_start_end_date(self):
    #     from configuration_settings.templatetags.configuration_tags import get_quarters
    #     financial_year = user_setup().get('financial_year', 0)
    #     start_date, end_date = None, None
    #     if self.periodicity == 1:
    #         start_date = datetime.now().date()
    #         end_date = datetime.now().date()
    #     elif self.periodicity == 2:
    #         start_date = (datetime.now() - timedelta(days=datetime.now().weekday())).date()
    #         end_date = datetime.now().date()
    #     elif self.periodicity == 3:
    #         start_date = datetime.now().date().replace(day=1)
    #         end_date = datetime.now().date()
    #     elif self.periodicity == 4:
    #         start_date, end_date = get_quarters((1, 4, 7, 10), datetime.now())
    #     elif self.periodicity == 5:
    #         quarter_tuple = (1, 7) if financial_year == 0 else (4, 10)
    #         start_date, end_date = get_quarters((1, 7), datetime.now())
    #     elif self.periodicity == 6:
    #         quarter_tuple = (1) if financial_year == 0 else (4)
    #         start_date, end_date = get_quarters(quarter_tuple, datetime.now())
    #     return start_date, end_date

    # def get_activity_project(self):
    #     project = None
    #     try:
    #         # from projectmanagement.models import Lineitem
    #         project = Lineitem.objects.get_or_none(activity=self).project
    #     except:
    #         pass
    #     return project

    #                                                         survey
    def __str__(self):
        # sets name as unicode
        return self.name

    # def get_unique_validations(self):
    #     try:
    #         question = SurveyUniqueQuestions.objects.get(survey=self)
    #     except:
    #         question = None
    #     return question

    def questions(self):
        # filtering all survey questions based on blocks
        return Question.objects.filter(block__survey=self, active=2)

    def onlyquestions(self):
        # filtering survey questions based on blocks
        return Question.objects.filter(block__survey=self, active=2, is_grid=False)

    def get_hash_code(self):
        return self.extra_config.get('hash_code')

    def get_blocks(self):
        # filtering survey questions based on blocks
        return Block.objects.filter(survey=self, active=2).order_by('block_order')

    def get_extended_profile_questions(self):
        questions = Question.objects.filter(active=2,is_profile=True,block__survey=self)
        return questions

    # def has_answers(self):
    #     """ bool returns true or false
    #     this returns whether particular block survey questions has answers"""
    #     if self.survey_type == 0:
    #         from beneficiary.models import BeneficiaryResponse
    #         return bool(BeneficiaryResponse.objects.filter(survey=self))
    #     else:
    #         return bool(JsonAnswer.objects.filter(survey=self))

    # #TODO: this is used in form configurations
    # def is_skip_survey(self):
    #     choices = Choice.objects.filter(
    #         active=2, skip_question__id__gt=0, question__block__survey=self)
    #     return True if choices else False

    # def get_beneficiary_location_details(self,survey_key,user):
    #     from beneficiary.models import BeneficiaryType
    #     from masterdata.models import BoundaryLevel
    #     order_levels, labels,beneficiary_type,beneficiary_ids = '','','',''
    #     benf_id_list = []
    #     benf_type_list =[]
    #     from configuration_settings.user_location_views import get_user_level
    #     from survey.new_apis import get_orders_levels,get_boundary_levels_orders
    #     user_level = get_user_level(user)
    #     if self.survey_type == 0:
    #         beneficiaryobj = BeneficiaryType.objects.get_or_none(id = self.object_id)
    #         beneficiary_ids = beneficiaryobj.get_survey().id
    #         beneficiary_type = beneficiaryobj.name
    #         if self.extra_config.get('user_level'):
    #             order_levels = ','.join(['level'+str(level.code) for level in BoundaryLevel.objects.filter(active=2,code__in=self.extra_config.get('user_level')).order_by('code')])
    #             labels = ','.join([level.name for level in BoundaryLevel.objects.filter(active=2,code__in=self.extra_config.get('user_level')).order_by('code')])
    #         else:
    #             order_levels , labels = get_orders_levels(user_level)
    #     else:
    #         for i in self.config:
    #             for key in i.keys():
    #                 indexvalue = key.split('_')[-1]
    #                 if i[key] == "BeneficiaryType":
    #                     beneficiaryobj = BeneficiaryType.objects.get_or_none(id=int(i.get('object_id_' + indexvalue)))
    #                     beneficiary_type = str(beneficiaryobj.name)
    #                     beneficiary_ids = int(beneficiaryobj.get_survey().id)
    #                     benf_id_list.append(beneficiary_ids)
    #                     benf_type_list.append(beneficiary_type)
    #                     order_levels , labels = get_orders_levels(user_level)
                        
    #                 elif i[key] == 'BoundaryLevel':
    #                     boundaryobj  = BoundaryLevel.objects.get_or_none(id = int(i.get('object_id_'+indexvalue)))
    #                     if boundaryobj:
    #                         order_levels ,labels = get_boundary_levels_orders(boundaryobj,user_level)
            
    #     if survey_key == 'facility':
    #         facility_ids = benf_id_list[1] if len(benf_id_list) > 1 else ''
    #         facility_type = benf_type_list[1] if len(benf_type_list) > 1 else ''
    #         return facility_ids,facility_type
    #     else:
    #         beneficiary_ids =  benf_id_list[0] if benf_id_list else beneficiary_ids
    #         beneficiary_type = benf_type_list[0] if benf_type_list else beneficiary_type
    #     return order_levels,labels,beneficiary_ids,beneficiary_type

    # def get_survey_activities(self):
    #     from beneficiary.models import BeneficiaryType
    #     survey_objs = Survey.objects.filter(active=2, survey_type=1)
    #     activities_list = []
    #     for survey in survey_objs:
    #         for i in survey.config:
    #             for key in i.keys():
    #                 indexvalue = key.split('_')[-1]
    #                 if i[key] == "BeneficiaryType":
    #                     beneficiaryobj = BeneficiaryType.objects.get_or_none(id=int(i.get('object_id_' + indexvalue)))
    #                     beneficiary_ids = int(beneficiaryobj.get_survey().id)
    #                     if str(self.id) == str(beneficiary_ids):
    #                         activities_list.append(survey.id)
    #     if activities_list:
    #         activities_list = survey_objs.filter(id__in=activities_list)
    #     return activities_list

    # def get_beneficiary_location_types(self):
    #     from beneficiary.models import BeneficiaryType
    #     from masterdata.models import BoundaryLevel
    #     data =boundary = benfi=''
        
    #     for json in self.config:
    #         for key in json.keys():
    #             ids = key.split('_')[-1]
    #             if json[key] == 'BeneficiaryType':
    #                 benf_type = BeneficiaryType.objects.get_or_none(id = int(json.get('object_id_'+ids)))
    #                 benfi = get_names(benf_type)
    #             if json[key] == 'BoundaryLevel':
    #                 boundary  = BoundaryLevel.objects.get_or_none(id = int(json.get('object_id_'+ids)))
    #                 boundary = get_names(boundary)
    #         data = boundary_benfi_details(boundary,benfi)
            
            
    #     return data                                    

    # def get_beneficiary_type(self):
    #     from beneficiary.models import BeneficiaryType
    #     beneficiary_type = None
    #     if self.survey_type == 0:
    #         beneficiary_type = BeneficiaryType.objects.get_or_none(id=self.object_id)
    #     elif self.survey_type == 1:
    #         for i in self.config:
    #             for key in i.keys():
    #                 indexvalue = key.split('_')[-1]
    #                 if i[key] == "BeneficiaryType":
    #                     beneficiary_type = BeneficiaryType.objects.get_or_none(id=int(i.get('object_id_' + indexvalue)))
    #     return beneficiary_type

#     def get_survey_location(self):
#         from beneficiary.models import BeneficiaryType
#         location_level = None
# #        if self.survey_type == 1:
#         # import ipdb; ipdb.set_trace()
#         for i in self.config:
#             for key in i.keys():
#                 indexvalue = key.split('_')[-1]
#                 if i[key] == "BoundaryLevel":
# #                	#kartik change code to id query
# #                    location_level = BoundaryLevel.objects.get_or_none(id=int(i.get('object_id_' + indexvalue)))
#                     location_level = BoundaryLevel.objects.get_or_none(id=int(i.get('object_id_' + indexvalue)))
#                     if not location_level:
#                         location_level = BoundaryLevel.objects.get_or_none(code=int(i.get('object_id_' + indexvalue)))
#         return location_level

    def get_survey_child_location(self):
        location_level = self.get_survey_location()
        if location_level and location_level.code == 7:
            location_level = BoundaryLevel.objects.get_or_none(code = int(location_level.code-2))
        elif location_level and not location_level.code == 1 :
            location_level = BoundaryLevel.objects.get_or_none(code = int(location_level.code-1))
        return location_level
    
    # def get_parent_links(self):
    #     linkages = []
    #     if self.survey_type == 0:
    #         from beneficiary.models import BeneficiaryLink
    #         beneficiary_linkage_list = BeneficiaryLink.objects.filter(content_type=ContentType.objects.get_for_model(self.get_beneficiary_type()), \
    #             object_id=self.get_beneficiary_type().id, relation=None)
    #         for links in beneficiary_linkage_list:
    #             child_survey = Survey.objects.get(content_type_id=links.content_type1_id,\
    #                 object_id=links.object_id1, survey_type=0)
    #             try:
    #                 summary_qid = ','.join(str(j) for j in
    #                                        SurveyDisplayQuestions.objects.get(survey=child_survey, display_type='1').questions)
    #             except:
    #                 summary_qid = ','.join([str(quest.id) for quest in
    #                                        Question.objects.filter(block__survey=child_survey, parent=None, qtype__in=['T', 'R', 'S', 'C'])[:3]])
    #             link_dict = {'form_type_id':child_survey.id, 'uuid':links.creation_key, \
    #                 "name":child_survey.name, 'summary_qid': summary_qid}
    #             linkages.append(link_dict)
    #     return linkages

    # def get_beneficiary_linkages(self):
    #     linkages = []
    #     if self.survey_type == 0:
    #         from beneficiary.models import BeneficiaryLink
    #         primary_relations = MasterLookUp.objects.filter(
    #             parent__slug="primary-relation")
    #         beneficiary_linkage_list = BeneficiaryLink.objects.filter(content_type=ContentType.objects.get_for_model(self.get_beneficiary_type()), \
    #             object_id=self.get_beneficiary_type().id, relation__in=primary_relations)
    #         for links in beneficiary_linkage_list:
    #             child_survey = Survey.objects.get(content_type_id=links.content_type1_id,\
    #                 object_id=links.object_id1, survey_type=0)
    #             link_dict = {'form_type_id':child_survey.id, 'uuid':links.creation_key, \
    #                 "name":child_survey.name, "relation_id": links.relation_id}
    #             if links.get_linkage_rule_engine() and links.get_linkage_rule_engine().rule_engine:
    #                link_dict['rule_set_json'] = get_linkage_rule_sets(links,0)
    #                link_dict['rule_set_json_or'] = get_linkage_rule_sets(links,1)
    #                link_dict['validation'] = get_skill_validation_rule_set(links)
    #             linkages.append(link_dict)
    #     return linkages

    # #TODO: Not used in subhiksha application
    # def get_draft_answers(self):
    #     skip_questions = list(set(Choice.objects.filter(
    #         question__block__survey=self).values_list('skip_question', flat=True)))
    #     if skip_questions:
    #         skip_questions.remove(None) 
    #     questions = Question.objects.filter(
    #         block__survey__id=self.id, mandatory=True).exclude(id__in=skip_questions)
    #     if questions:
    #         first_id = questions.first().id
    #         last_id = questions.last().id
    #         json_answer = JsonAnswer.objects.filter(
    #             survey=self).values_list('response', 'id')
    #         exclude_list = []
    #         for el, ek in json_answer:
    #             try:
    #                 if not (el.get(str(first_id),'') and el.get(str(last_id),'')):
    #                     exclude_list.append(ek)
    #             except:
    #                 pass
    #         return exclude_list
    #     return []

    # def get_skip_questions(self):
    #     question_ids = []
    #     for question in self.questions():
    #         if question.is_skip_question():
    #             question_ids.append(question.id)
    #     return question_ids

    # def get_display_all_questions(self):
    #     question_ids =[]
    #     skip_questions = self.get_initial_question()
    #     questions = Question.objects.filter(parent=None, block__survey=self, \
    #             address_question=False, active=2).exclude(qtype__in=['AW']).exclude(id__in=skip_questions).order_by('code')
    #     return questions
    
    #TODO: used in same model method 
    def get_initial_question(self):
        question_ids = []
        for question in self.questions():
            choices = Choice.objects.filter(question=question)
            for i in question.get_choices():
                for j in i.skip_question.all():
                    question_ids.append(j.id)
        questions = [i.id for i in Question.objects.filter(block__survey=self, id__in=question_ids).order_by('question_order')]
        return questions
    
    def get_initial_questions_show(self,questions=None):
        if not questions:
          questions =self.questions().filter(parent=None,address_question=False, active=2).exclude(qtype__in=['AW','H']).order_by('code')
        question_ids = []
        for question in questions:
            question_ids.append(question)
            if question.is_skip_question() == True:
                break
        return question_ids
            
    #TODO: Not used in subhiksha application 
    def display_skip_questions(self):
        choice_dict = {}
        for question in self.questions():
            choices = Choice.objects.filter(question=question)
            for i in question.get_choices():
                question_ids = []
                for j in i.skip_question.all():
                    question_ids.append(j.id)
                choice_dict.update({i.id: question_ids})
        return choice_dict

    #TODO: Not used in subhiksha application 
    def hide_skip_questions(self):
        hide_dict = {}
        for question in self.questions():
            choices = Choice.objects.filter(question=question)
            for i in question.get_choices():
                question_ids = []
                for j in i.skip_question.all():
                    question_ids.append(j.id)
                hide_dict.update({i.id: [temp.id for temp in Question.objects.filter(code__gt=question.code, id__in=question.get_inner_questions()).exclude(id__in=question_ids)]})
        return hide_dict

    #TODO: Not used in subhiksha application 
    def hide_question_if_not_value(self):
        question_no_value_dict = {}
        for question in self.questions():
            question_no_value_dict.update({question.id: question.get_inner_questions()})
        return question_no_value_dict

    # #TODO: Not used in anywhere
    # def get_users_locations(self):
    #     # from projectmanagement.models import Lineitem,Project,ProjectUserRelation
    #     from userroles.models import (OrganizationLocation,)
    #     project_locations,user_locations,project_users = [],[],[]
    #     project_ids = list(set(Lineitem.objects.filter(activity = self,active=2).values_list("project_id",flat=True)))
    #     if project_ids:
    #         project_locations = filter(None,list(set(Project.objects.filter(id__in = project_ids).values_list("state__id",flat=True))))
    #         user_locations = filter(None,list(set(OrganizationLocation.objects.filter(project__id__in = project_ids).values_list("location__id",flat=True))))
    #         project_users = filter(None,list(set(ProjectUserRelation.objects.filter(project__id__in = project_ids).values_list("user__user",flat=True))))
    #     return project_locations,user_locations,project_users

    # #TODO: Not used in anywhere
    # def get_locations_on_users(self,common_user_ids):
    #     from userroles.models import (OrganizationLocation,)
    #     # from projectmanagement.models import Lineitem,Project,ProjectUserRelation
    #     user_locations = []
    #     project_ids = list(set(Lineitem.objects.filter(activity = self,active=2).values_list("project_id",flat=True)))
    #     if project_ids:
    #         user_locations = filter(None,list(set(OrganizationLocation.objects.filter(project__id__in = project_ids,user__user__id__in = common_user_ids).values_list("location__id",flat=True))))
    #     return user_locations

    #TODO: Not used in subhiksha application 
    def get_surey_responses(self):
        responses_list = JsonAnswer.objects.filter(survey=self)
        result = {'responses_list':responses_list,'total':responses_list.count()}
        return result
    
    def get_search_filter_ids(self):
        obj = SurveyDisplayQuestions.objects.get_or_none(display_type='3',survey__id=self.id)
        if obj :
            questions = ','.join(map(str,obj.questions))
        else:
            questions = ''
        return questions


###{"type":"location","reference_to":"188","value":"2018,1202","reference_question_id":"1234","data_type":"location","level":4,"operator":"IN"}
    #TODO: Not used in subhiksha application but used in some api call/ rule set is not using
    def get_survey_rule_beneficiary(self):
        # this is for rule based of location based surveys.
        rule_engine_data = []
        if self.get_survey_rule_engine() and self.get_survey_rule_engine().rule_engine.get('location_based_survey'):
            for counter, rulesets in enumerate(self.get_survey_rule_engine().rule_engine.get('location_based_survey')):
                if rulesets.get("type") == "location":
                    question_id = rulesets.get("reference_question_id")
                    value = rulesets.get("value")
                    data_type = rulesets.get('data_type')
                    level = rulesets.get('level')
                    operator = rulesets.get('operator')
                    rule_engine_data.append({"data_type":data_type,"operator":operator,"question_id":str(question_id),"value":value,"level":level})
                elif rulesets.get("type") == "value":
                    question_id = rulesets.get("reference_question_id")
                    value = rulesets.get("value")
                    operator = rulesets.get('operator')
                    try:
                        rule_engine_data.append({"data_type":"String","operator":str(operator),"question_id":str(question_id),"value": str(value),"level":0})
                    except:
                        pass
        return rule_engine_data
    
    #TODO: Not used in subhiksha application 
#     def get_survey_category_rule_set(self):
#         ### this for showing the rules sets based on the choice selected in the beneficiary .to show it in category wise
#         rule_engine_data = []
#         if self.get_survey_rule_engine() and self.get_survey_rule_engine().rule_engine.get('category_survey'):
#             for counter, rulesets in enumerate(self.get_survey_rule_engine().rule_engine.get('category_survey')):
#                 if rulesets.get("type") == "categories":
#                     question_id = rulesets.get("reference_question_id")
#                     value = rulesets.get("value")
#                     data_type = rulesets.get('type')
#                     level = rulesets.get('level',0)
#                     operator = rulesets.get('operator',"==")
#                     category_ids = rulesets.get('category_ids')
#                     category_names = ','.join(MasterLookUp.objects.filter(id__in=category_ids.split(',')).values_list('name',flat=True))
#                     global_category = rulesets.get('global_category','')
#                     allowed_loc = rulesets.get('allowed_loc','')
#                     rule_engine_data.append({"data_type":data_type,"operator":operator,"question_id":str(question_id),"value":value,"level":level,"category_ids":category_ids,"category_names":category_names,'global_category':global_category,
#                     'allowed_loc':allowed_loc})
#                 elif rulesets.get("type") == "value":
#                     question_id = rulesets.get("reference_question_id")
#                     value = rulesets.get("value")
#                     operator = rulesets.get('operator')
#                def get_survey_category_rule_set(self):
#         ### this for showing the rules sets based on the choice selected in the beneficiary .to show it in category wise
#         rule_engine_data = []
#         if self.get_survey_rule_engine() and self.get_survey_rule_engine().rule_engine.get('category_survey'):
#             for counter, rulesets in enumerate(self.get_survey_rule_engine().rule_engine.get('category_survey')):
#                 if rulesets.get("type") == "categories":
#                     question_id = rulesets.get("reference_question_id")
#                     value = rulesets.get("value")
#                     data_type = rulesets.get('type')
#                     level = rulesets.get('level',0)
#                     operator = rulesets.get('operator',"==")
#                     category_ids = rulesets.get('category_ids')
#                     category_names = ','.join(MasterLookUp.objects.filter(id__in=category_ids.split(',')).values_list('name',flat=True))
#                     global_category = rulesets.get('global_category','')
#                     allowed_loc = rulesets.get('allowed_loc','')
#                     rule_engine_data.append({"data_type":data_type,"operator":operator,"question_id":str(question_id),"value":value,"level":level,"category_ids":category_ids,"category_names":category_names,'global_category':global_category,
#                     'allowed_loc':allowed_loc})
#                 elif rulesets.get("type") == "value":
#                     question_id = rulesets.get("reference_question_id")
#                     value = rulesets.get("value")
#                     operator = rulesets.get('operator')
#                     try:
#                         rule_engine_data.append({"data_type":"String","operator":str(operator),"question_id":str(question_id),"value": str(value),"level":0})
#                     except:
#                         pass
#         return rule_engine_data
        
#     #TODO: Not used in subhiksha application 
#     def get_survey_linkage_questions(self):
#         rule_engine_data = []
#         if self.get_survey_rule_engine() and self.get_survey_rule_engine().rule_engine.get('survey_linkages'):
#             for counter, rulesets in enumerate(self.get_survey_rule_engine().rule_engine.get('survey_linkages')):
#                 if rulesets.get("type") == "survey_linkages":
#                     question_id = rulesets.get("reference_question_id")
#                     value = rulesets.get("value")
#                     data_type = rulesets.get('type')
#                     rule_engine_data.append(value)
#                 elif rulesets.get("type") == "value":
#                     question_id = rulesets.get("reference_question_id")
#                     value = rulesets.get("value")
#                     operator = rulesets.get('operator')
#                     try:
#                         rule_engine_data.append({"data_type":"String","operator":str(operator),"question_id":str(question_id),"value": str(value),"level":0})
#                     except:
#                         pass
#         return rule_engine_data
        
#     #TODO: Not used in subhiksha application 
#     def get_form_questions(self):
#         obj = SurveyDisplayQuestions.objects.get_or_none(survey=self.id,display_type=1)
#         questions = Question.objects.filter(id__in=obj.questions) if obj else []
#         return questions
        
#     def is_beneficiary_based_child(self):
#         # this is to get the beneficiary address where the child beneficiary doesnt have address question
#         # child beneficiary is saved based on beneficiary_address.
#         #TO check the child beneficiary has address qquestion and 
#         #if parent beneficiary is api type in child beneficiary this function is used
#        status = Question.objects.filter(block__survey=self,api_json__is_beneficiary_ques=2).exists()
#        return status

#     # #TODO: Not used in subhiksha application 
#     # def get_parent_beneficiary_address(self):
#     #     from beneficiary.models import BeneficiaryType
#     #     ques = Question.objects.get_or_none(block__survey=self,api_json__is_beneficiary_ques=2)
#     #     if ques:
#     #         benef_id = ques.api_json.get('parent_beneficiary_id')
#     #         ben_obj = BeneficiaryType.objects.get_or_none(id=benef_id)
#     #         survey = Survey.objects.get(survey_type=0,content_type = ContentType.objects.get_for_model(ben_obj),object_id=ben_obj.id)
#     #         qid = survey.questions().filter(qtype='AW')[0]
#     #     else:
#     #         qid = None
#     #     return qid

# def get_linkage_rule_sets(links,key):
#     survey_dict = {'0':'score_based_survey','1':'score_based_survey_or'}
#     key_value = survey_dict.get(str(key))
#     rule_engine_data = []
#     if links.get_linkage_rule_engine().rule_engine.get(key_value):
#         for counter, rulesets in enumerate(links.get_linkage_rule_engine().rule_engine.get(key_value)):
#             if rulesets.get("type") == "score":
#                 age_question_id = rulesets.get("reference_question_id")
#                 try:
#                     split_text = rulesets.get("score").split('-')
#                     if split_text[1]:
#                         rule_engine_data.append({"data_type":"Number","operator":">=","question_id":str(age_question_id),"value": str(split_text[0])})
#                         rule_engine_data.append({"data_type":"Number","operator":"<=","question_id":str(age_question_id),"value": str(split_text[1])})
#                 except:
#                     pass
#                 try:
#                     split_text = rulesets.get("score").split('>')
#                     if split_text[1]:
#                         rule_engine_data.append({"data_type":"Number","operator":">","question_id":str(age_question_id),"value": str(split_text[1])})        
#                 except:
#                     split_text = rulesets.get("score").split('<')
#                     try:
#                         if split_text[1]:
#                             rule_engine_data.append({"data_type":"Number","operator":"<","question_id":str(age_question_id),"value": str(split_text[1])})    
#                     except:
#                         pass 
#             elif rulesets.get("type") == "value":
#                 age_question_id = rulesets.get("reference_question_id")
#                 value          try:
#                         rule_engine_data.append({"data_type":"String","operator":str(operator),"question_id":str(question_id),"value": str(value),"level":0})
#                     except:
#                         pass
#         return rule_engine_data
        
#     #TODO: Not used in subhiksha application 
#     def get_survey_linkage_questions(self):
#         rule_engine_data = []
#         if self.get_survey_rule_engine() and self.get_survey_rule_engine().rule_engine.get('survey_linkages'):
#             for counter, rulesets in enumerate(self.get_survey_rule_engine().rule_engine.get('survey_linkages')):
#                 if rulesets.get("type") == "survey_linkages":
#                     question_id = rulesets.get("reference_question_id")
#                     value = rulesets.get("value")
#                     data_type = rulesets.get('type')
#                     rule_engine_data.append(value)
#                 elif rulesets.get("type") == "value":
#                     question_id = rulesets.get("reference_question_id")
#                     value = rulesets.get("value")
#                     operator = rulesets.get('operator')
#                     try:
#                         rule_engine_data.append({"data_type":"String","operator":str(operator),"question_id":str(question_id),"value": str(value),"level":0})
#                     except:
#                         pass
#         return rule_engine_data
        
#     #TODO: Not used in subhiksha application 
#     def get_form_questions(self):
#         obj = SurveyDisplayQuestions.objects.get_or_none(survey=self.id,display_type=1)
#         questions = Question.objects.filter(id__in=obj.questions) if obj else []
#         return questions
        
#     def is_beneficiary_based_child(self):
#         # this is to get the beneficiary address where the child beneficiary doesnt have address question
#         # child beneficiary is saved based on beneficiary_address.
#         #TO check the child beneficiary has address qquestion and 
#         #if parent beneficiary is api type in child beneficiary this function is used
#        status = Question.objects.filter(block__survey=self,api_json__is_beneficiary_ques=2).exists()
#        return status

#     # #TODO: Not used in subhiksha application 
#     # def get_parent_beneficiary_address(self):
#     #     from beneficiary.models import BeneficiaryType
#     #     ques = Question.objects.get_or_none(block__survey=self,api_json__is_beneficiary_ques=2)
#     #     if ques:
#     #         benef_id = ques.api_json.get('parent_beneficiary_id')
#     #         ben_obj = BeneficiaryType.objects.get_or_none(id=benef_id)
#     #         survey = Survey.objects.get(survey_type=0,content_type = ContentType.objects.get_for_model(ben_obj),object_id=ben_obj.id)
#     #         qid = survey.questions().filter(qtype='AW')[0]
#     #     else:
#     #         qid = None
#     #     return qid

# def get_linkage_rule_sets(links,key):
#     survey_dict = {'0':'score_based_survey','1':'score_based_survey_or'}
#     key_value = survey_dict.get(str(key))
#     rule_engine_data = []
#     if links.get_linkage_rule_engine().rule_engine.get(key_value):
#         for counter, rulesets in enumerate(links.get_linkage_rule_engine().rule_engine.get(key_value)):
#             if rulesets.get("type") == "score":
#                 age_question_id = rulesets.get("reference_question_id")
#                 try:
#                     split_text = rulesets.get("score").split('-')
#                     if split_text[1]:
#                         rule_engine_data.append({"data_type":"Number","operator":">=","question_id":str(age_question_id),"value": str(split_text[0])})
#                         rule_engine_data.append({"data_type":"Number","operator":"<=","question_id":str(age_question_id),"value": str(split_text[1])})
#                 except:
#                     pass
#                 try:
#                     split_text = rulesets.get("score").split('>')
#                     if split_text[1]:
#                         rule_engine_data.append({"data_type":"Number","operator":">","question_id":str(age_question_id),"value": str(split_text[1])})        
#                 except:
#                     split_text = rulesets.get("score").split('<')
#                     try:
#                         if split_text[1]:
#                             rule_engine_data.append({"data_type":"Number","operator":"<","question_id":str(age_question_id),"value": str(split_text[1])})    
#                     except:
#                         pass 
#             elif rulesets.get("type") == "value":
#                 age_question_id = rulesets.get("reference_question_id")
#                 value = rulesets.get("value")
#                 try:
#                     rule_engine_data.append({"data_type":"String","operator":"==","question_id":str(age_question_id),"value": str(value)})
#                 except:
#                     pass
#     return rule_engine_data
    
# def get_skill_validation_rule_set(links):
#     rule_engine_data = []
#     if links.get_linkage_rule_engine().rule_engine.get('linkage_validation'):
#         for counter, rulesets in enumerate(links.get_linkage_rule_engine().rule_engine.get('linkage_validation')):
            
#             if rulesets.get("type") == "validation":
#                 parent_question_id = rulesets.get("reference_question_id")
#                 value = rulesets.get("value")
#                 child_question_id = rulesets.get("child_question_id")
#                 is_skill_based = rulesets.get('is_skill_based')
#                 duplication = rulesets.get('duplication')
#                 try:
#                     rule_engine_data.append({"parent_question_id":str(parent_question_id),"is_skill_based":is_skill_based,"child_question_id":str(child_question_id),"can_allow_duplication":duplication})
#                 except:
#                     pass
    # return rule_engine_data

class Block(BaseContent):
    #                                                          Block
    # survey is based on blocks
    # so survey is a foreign key
    # Block type is giving as choices

    survey = models.ForeignKey(Survey,on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=500, blank=False, null=False)
    block_order = models.IntegerField(null=True, blank=True)
    code = models.IntegerField(default=0)
    language_code = models.JSONField(default=dict,**OPTIONAL)

    def __str__(self):
        # sets name as unicode
        return self.name

    # def get_questions(self):
    #     # Caching the questions based on block
    #     # filtering block based questions
    #     cache_key_questions = f'{INSTANCE_CACHE_PREFIX}get_questions_{self.id}'
    #     block_based_questions =  cache.get(cache_key_questions)
    #     if not block_based_questions:
    #         block_based_questions=Question.objects.filter(block=self, active=2).order_by('question_order')
    #         cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_questions,block_based_questions,CACHES.get("default")['DEFAULT_SHORT_DURATION'])
        
    #     return block_based_questions


QTYPE_CHOICES = (
        ('T', 'Text Input'), ('S', 'Select One Choice'), ('R', 'Radio List'),
        ('C', 'Checkbox List'), ('D', 'Date'), ('I', 'Image'),('GD', 'Grid with fixed rows'),
        ('In', 'Grid with vis_skip_questionariable rows'), ('AW', 'Address Widget'),
        ('AI', 'API'), ('F', 'File'), ('TA', 'Text Area'),('AF','AutoFill and Calculate'),('H','Hidden Question'),('AP','Auto Populate'),
    ('TM','Time Widget'),('SM','Select MasterLookup'),)
API_QTYPE_CHOICES = (('S', 'Select One Choice'), ('R', 'Radio List'),
        ('C', 'Checkbox List'),('T','Text'),('RO','Read Only'))

QUESTION_DEACTIVATE_REASON = (("Program Discontinued","Program Discontinued"), ("Program Major Revamp","Program Major Revamp"), ("Others","Others"))

class Question(BaseContent):
    #                                                          Question
    # In survey we have multiple type of questions
    # eg for text input: what is your name?F
    # eg for select one choice : gender= male or female
    # Radio List:This question type collects input from a list of radio buttons
    # Checkbox list : provides a multi selection check box group
    # that can be dynamically generated with data binding.
    # setting validation type option for questions
    VALIDATION_CHOICES = (
        (0, 'Digit'), (1, 'Number'), (2, 'Alphabet'),
        (3, 'Alpha Numeric'), (4, 'No Validation'), (6, 'Mobile Number'),
        (7, 'Landline'), (8, 'Date'), (9, 'Time'), (10, 'Only Alpha Numeric')

    )
    META_TYPE_CHOICES = (
        (0, 'Normal'), (1, 'Village Name'), (2, 'Customer Id'),
        (3, 'Piriodicity'), (4, 'Consent Status'), (5, 'Ruban Code')
    )
    QT_FILTER_CHOICES = ((0,'No'),(1,'Yes'))
    

    block = models.ForeignKey(Block, verbose_name=_('Blocks'),on_delete=models.DO_NOTHING)
    qtype = models.CharField(_('question type'), max_length=2,
                             choices=QTYPE_CHOICES)
    api_qtype = models.CharField(_('api question type'), max_length=2,
                             choices=API_QTYPE_CHOICES, blank=True, null=True)
    text = models.CharField(_('question text'), max_length=500)
    validation = models.IntegerField(choices=VALIDATION_CHOICES,
                                     blank=True, null=True)
    question_order = models.IntegerField(null=True, blank=True)
    code = models.IntegerField(default=0)
    help_text = models.CharField(max_length=500, blank=True)
    parent = models.ForeignKey('self', blank=True, null=True,on_delete=models.DO_NOTHING)

    mandatory = models.BooleanField(default=True)
    display = models.PositiveIntegerField(default=0)
    hidden = models.PositiveIntegerField(default=0)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    is_profile = models.BooleanField(default=False)
    is_grid = models.BooleanField(default=False)
    language_code = models.JSONField(default=dict,**OPTIONAL)
    master_question = models.ForeignKey(MasterLookUp,
             null=True, blank=True,on_delete=models.DO_NOTHING)
    display_inline = models.BooleanField(default=False)
    address_question = models.BooleanField(default=False)
    allow_multiple = models.BooleanField(default=False)
    api_json = models.JSONField('API Json', default=dict, **OPTIONAL)
    display_has_name = models.BooleanField(default=False) #used to display names in beneficiary parent listing
    parent_question = models.BooleanField(default=False) #used to retrieve question based on childs
    is_editable = models.BooleanField(default=True)
    training_config = models.JSONField('Training configuration', default=dict, **OPTIONAL)
    code_display = models.CharField(max_length=200,null=True, blank=True)
    ACTIVE_CHOICES = ((0, 'Inactive'), (2, 'Active'),)
    question_filter = models.PositiveIntegerField('Show as filter',choices=QT_FILTER_CHOICES,default=0)
    short_text = models.CharField(max_length=500, blank=True,null=True)
    deactivated_reason = models.CharField(max_length=500,blank=True,null=True,choices=QUESTION_DEACTIVATE_REASON)
    deactivated_date   = models.DateTimeField(blank=True, null=True)
    deactivated_user   = models.ForeignKey(User, blank=True, null=True,on_delete=models.DO_NOTHING)
    #used for show the number indicator in the forms
    form_question_number = models.CharField(max_length=20,blank=True,null=True)

    def name(self):
#       # returns text
        return self.text

    def __str__(self):
        #                                                         Question
        # sets name as unicode
        return "%s - %s---(%s)" % (self.text, self.code, self.block.survey)

    #TODO: Not used anywhere in subhiksha 
    def question_text_lang(self,lid=1):
        try:
            return self.text if int(lid) == 1 else self.language_code[str(lid)]
        except Exception as e:
            return self.text

    #TODO: Not used anywhere in subhiksha 
    def get_question_languages(self):
        return LanguageTranslationText.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id, active=2)

    # def choice_list(self,lid=1):
    #     from configuration_settings.form_views import load_data_to_cache_choices
    #     choice_cache_dict = load_data_to_cache_choices()
    #     question_ids = []
        
        # choices = Choice.objects.filter(question__id=self.id).exclude(active=0)
        # if self.qtype not in ['R','S','C']:
        #     return []
        # elif choices:
        #     choice_list = []
        #     for i in choices:
        #         skip_question_ids = []
        #         choice_dict = {"id": i.id,"disabled":i.config.get('disable'), "choice": i.text if int(lid) ==1 else i.language_code[str(lid)]}
        #         for j in i.skip_question.all():
        #             skip_question_ids.append(j.id)
        #         choice_dict.update({"skip_question_ids": skip_question_ids})
        #         choice_list.append(choice_dict)
        # return choice_cache_dict.get(str(self.id))

    #TODO: Not used anywhere in subhiksha 
    def choicelist(self):
        choices = Choice.objects.filter(question__id=self.id)
        return choices

    #TODO: Not used anywhere all application
    def next_question_choice_list(self):
        choices = Choice.objects.filter(question__id=self.id)
        skip_question_ids = []

    #TODO:choicelist same function 
    def get_choices(self):
        choices = Choice.objects.filter(question__id=self.id)
        return choices
    
    #TODO: Not used anywhere subhiksha
    def is_other_question(self):
        return self.get_choices().filter(is_other_choice=True)

    # def get_childs(self):
    #     # Caching the child questions based on parent question
    #     # filtering block based questions
    #     cache_key_questions = f'{INSTANCE_CACHE_PREFIX}get_childs_old_{self.id}'
    #     parent_based_questions =  cache.get(cache_key_questions)
    #     if not parent_based_questions:
    #         parent_based_questions=Question.objects.filter(parent=self,active=2).order_by('question_order')
    #         cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_questions,parent_based_questions,CACHES.get("default")['DEFAULT_SHORT_DURATION'])
        
    #     return parent_based_questions

    # def is_skip_question(self):
    #     from configuration_settings.form_views import load_data_to_cache_choices
    #     choice_cache_dict = load_data_to_cache_choices()
    #     next_question_choices = choice_cache_dict.get(str(self.id),[])
    #     for k in next_question_choices:
    #         if k.get('skip_question_ids'):
    #             # has_skip_questions = True
    #             return True
    #     return False
        # choice = Choice.objects.filter(question=self)
        # if choice:
        #     for i in choice:
        #         if i.skip_question.all():
        #             return True
        #     return False
        # else:
        #     return False

    #TODO: Need to add cache for question validations
    def get_validation(self):
        return QuestionValidation.objects.get_or_none(question_id=self.id)

    # def get_validation_code(self):
    #     from configuration_settings.form_views import load_data_to_cache_question_validation
    #     questions = load_data_to_cache_question_validation()
    #     # questions = [questions.get(str(self.id),{})]
    #     # questions = QuestionValidation.objects.filter(question=self)
    #     min_max_dict = {'min_length': '', 'max_length': '', 'min': '',
    #                        'max': ''}
    #     validation_dict = {}
    #     # "charactersType": [i.get('id') for i in questions if questions]
    #     # for i in questions:
    #     i = questions.get(str(self.id))
    #     if i and i.get('code') == 'A' or i.get('code') == 'AN':
    #         min_max_dict.update({'min_length': literal_eval(i.get('min_value')), 'max_length':
    #             literal_eval(i.get('max_value'))})
    #     elif i and i.get('code') == 'N':
    #         min_max_dict.update({'min': literal_eval(i.get('min_value')), 'max':
    #             literal_eval(i.get('max_value'))})
    #     elif i and i.get('code') == 'DT' and i.get('min_value') and i.get('max_value'):
    #         min=i.get('min_value')[4:]+'-'+i.get('min_value')[2:4]+'-'+i.get('min_value')[:2] if i.get('min_value') != '00000000' else datetime.today().strftime("%Y-%m-%d")
    #         max=i.get('max_value')[4:]+'-'+i.get('max_value')[2:4]+'-'+i.get('max_value')[:2] if i.get('max_value') != '00000000' else datetime.today().strftime("%Y-%m-%d")
    #         min_max_dict.update({'min': min, 'max':max})
    #     validation_dict.update({'MinMax': min_max_dict})
    #     return validation_dict

    # #TODO: Used in question configurations
    # def get_skip_question_ids(self, survey=None, parent=None):
    #     question_ids = []
    #     choice = Choice.objects.filter(
    #         question__block__survey=survey, question__parent=parent)
    #     for i in choice:
    #         for j in i.skip_question.all():
    #             question_ids.append(j.id)
    #     return list(set(question_ids))

    # def get_inner_questions(self):
    #     from configuration_settings.form_views import load_data_to_cache_choices

    #     question_ids = []
    #     choice_cache_dict =  load_data_to_cache_choices()
    #     choice  = choice_cache_dict.get(str(self.id),[])
    #     for i in choice:
    #         for j in i.get('skip_question_ids'):
    #             question_ids.append(j)
    #             has_skip_questions = False
    #             next_question_choices = choice_cache_dict.get(str(j),[])
    #             for k in next_question_choices:
    #                 if k.get('skip_question_ids'):
    #                     has_skip_questions = True
    #             if has_skip_questions:
    #                 next_question = Question.objects.get(id = j)
    #                 question_ids.extend(next_question.get_inner_questions())
    #     return list(set(question_ids))

    def get_row_questions(self):
        row_list = Question.objects.filter(parent=self, is_grid=True)
        return row_list

    def get_column_questions(self):
        row_list = Question.objects.filter(parent=self, is_grid=False,active=2)
        return row_list

    #TODO: Not used in subhiksha application
    # def get_column_row_grid_questions(self, answers, add_or_edit):
    #     from survey.survey_form_newapis import get_grid_question_answer
    #     row_list = Question.objects.filter(parent=self,is_grid=True)
    #     final_list = []
    #     for row in row_list:
    #         row_dict = {'id': row.id, 'name':row.text, 'order':
    #             row.question_order}
    #         column_list = Question.objects.filter(parent=self, is_grid=False)
    #         row_column_list = []
    #         grids_skip_questions = self.get_skip_question_ids(
    #             self.block.survey, self)
    #         for column in column_list:
    #             question_dict = {"questionType": column.qtype,
    #                              "questionMandatory": str(column.mandatory),
    #                              "questionLabel": column.question_text_lang(
    #                                  1),
    #                              "questionId": column.id,
    #                              "questionError": "",
    #                              "questionAnswer": get_grid_question_answer(
    #                                  self, row, column, answers),
    #                              "questionChoice": column.choice_list(1),
    #                              "AllowMultiple": str(column.allow_multiple),
    #                              "AddressQuestion": str(
    #                                  column.address_question),
    #                              "questionAPI": column.api_json,
    #                              "questionAnswerText": "",
    #                              "blockId": column.block_id,
    #                              "blockName": column.block.name \
    #                                  if column.block else "",
    #                              "isSkip": str(column.is_skip_question()),
    #                              "gridQuestions": [],
    #                              "isQuestionShow": 0 if column.id in
    #                                                        grids_skip_questions else 1, "add_or_edit": add_or_edit
    #                              }
    #             question_dict['constraints'] = column.get_validation_code()
    #             row_column_list.append(question_dict)
    #         row_dict.update({"questions": row_column_list})
    #         final_list.append(row_dict)
    #     return final_list


    #TODO: Not used in subhiksha application
    # def get_inline_questions(self, answers, add_or_edit):
    #     from survey.survey_form_newapis import get_inline_question_answer
    #     column_list = Question.objects.filter(parent=self)
    #     final_list = []
    #     grids_skip_questions = self.get_skip_question_ids(
    #         self.block.survey, self)
    #     if not answers:
    #         row = [1]
    #     else:
    #         try:
    #             row = answers.response.get(str(self.id)).keys()
    #         except:
    #             row = [1]
    #     for row in row:
    #         question_list = []
    #         for column in column_list:
    #             question_dict = {"questionType": column.qtype,
    #                              "questionMandatory": str(column.mandatory),
    #                              "questionLabel": column.question_text_lang(
    #                                  1),
    #                              "questionId": column.id,
    #                              "questionError": "",
    #                              "questionAnswer": get_inline_question_answer(
    #                                  self, row, column, answers),
    #                              "questionChoice": column.choice_list(1),
    #                              "AllowMultiple": str(column.allow_multiple),
    #                              "AddressQuestion": str(
    #                                  column.address_question),
    #                              "questionAPI": column.api_json,
    #                              "questionAnswerText": "",
    #                              "blockId": column.block_id,
    #                              "blockName": column.block.name \
    #                                  if column.block else "",
    #                              "isSkip": str(column.is_skip_question()),
    #                              "gridQuestions": [],
    #                              "isQuestionShow": 0 if column.id in
    #                                                     grids_skip_questions
    #         else 1, "add_or_edit": add_or_edit
    #                              }
    #             question_dict['constraints'] = column.get_validation_code()
    #             question_list.append(question_dict)
    #         data_dict = {"id": row, "questions": question_list}
    #         final_list.append(data_dict)
    #     return final_list

    # #TODO: Not used in subhiksha application
    # def get_skip_questions(self):
    #     question_ids = []
    #     if self.qtype in ['GD', 'In']:
    #         for question in Question.objects.filter(parent=self, is_grid=False, active=2):
    #             if question.is_skip_question():
    #                 question_ids.append(question.id)
    #     return question_ids

    # #TODO: Not used in subhiksha application
    # def get_initial_question(self):
    #     question_ids = []
    #     if self.qtype in ['GD', 'In']:
    #         for question in Question.objects.filter(parent=self, is_grid=False, active=2):
    #             choices = Choice.objects.filter(question=question)
    #             for i in question.get_choices():
    #                 for j in i.skip_question.all():
    #                     question_ids.append(j.id)
    #     questions = [i.id for i in Question.objects.filter(parent=self, id__in=question_ids).order_by('question_order')]
    #     return questions

    # #TODO: Not used in subhiksha application
    def display_skip_questions(self):
        choice_dict = {}
        if self.qtype in ['GD', 'In']:
            for question in Question.objects.filter(parent=self, is_grid=False, active=2):
                choices = Choice.objects.filter(question=question)
                for i in question.get_choices():
                    question_ids = []
                    for j in i.skip_question.all():
                        question_ids.append(j.id)
                    choice_dict.update({i.id: question_ids})
        return choice_dict

    #TODO: Not used in subhiksha application
    def hide_skip_questions(self):
        hide_dict = {}
        if self.qtype in ['GD', 'In']:
            for question in Question.objects.filter(parent=self, is_grid=False, active=2):
                choices = Choice.objects.filter(question=question)
                for i in question.get_choices():
                    question_ids = []
                    for j in i.skip_question.all():
                        question_ids.append(j.id)
                    hide_dict.update({i.id: [temp.id for temp in Question.objects.filter(code__gt=question.code, id__in=question.get_inner_questions()).exclude(id__in=question_ids)]})
        return hide_dict

    #TODO: Not used in subhiksha application
    def hide_question_if_not_value(self):
        question_no_value_dict = {}
        if self.qtype in ['GD', 'In']:
            for question in Question.objects.filter(parent=self, is_grid=False, active=2):
                question_no_value_dict.update({question.id: question.get_inner_questions()})
        return question_no_value_dict

    class Meta:
        # Question
        # Don't create a table in database
        # This table is abstract
        ordering = ('block', 'question_order')

CHOICE_DEACTIVATE_REASON = (("Program Discontinued","Program Discontinued"), ("Program Major Revamp","Program Major Revamp"), ("Others","Others"))
class Choice(BaseContent):
    #                                                          choice
    # question has choices
    question = models.ForeignKey(Question, related_name='choices',
                                 verbose_name=_('question'), blank=True, null=True,on_delete=models.DO_NOTHING,)
    text = models.CharField(_('choice text'), max_length=500)
    code = models.IntegerField()
    choice_order = models.FloatField(blank=True)
    skip_question = models.ManyToManyField(Question, related_name='skip_question')
    language_code = models.JSONField(default=dict,**OPTIONAL)
    is_other_choice = models.BooleanField(default=False)
    config = models.JSONField('Configurations', default=dict, **OPTIONAL)
    code_display = models.IntegerField(default=0,null=True, blank=True)
    score = models.FloatField(default=0,null=True, blank=True)
    # boundary=models.ManyToManyField(Boundary)
    uuid = models.CharField('UUID', max_length=100,blank=True,null=True)
    deactivated_reason = models.CharField(max_length=500,blank=True,null=True,choices=CHOICE_DEACTIVATE_REASON)
    deactivated_date   = models.DateTimeField(blank=True, null=True)
    deactivated_user   = models.ForeignKey(User, blank=True, null=True,on_delete=models.DO_NOTHING)

    def save(self, *args, **kwargs):
        self.choice_order = self.code
        super(Choice, self).save(*args, **kwargs)

    def name(self):
        #                                                          choice
        # returns text
        return self.text


    def get_text_choices_rule_engine(self):
        rule_engine_data = []
        if self.question and self.question.qtype in ['T']:
            split_text = self.text.split('-')
            try:
                rule_engine_data = [{"data_type":"Number","operator":">=","question_id":int(self.question.id),"value": str(split_text[0])}, 
                        {"data_type":"Number","operator":"<=","question_id":int(self.question.id),"value": str(split_text[1])}]
            except:
                pass
            if not rule_engine_data:
                split_text = self.text.split('>')
                try:
                    rule_engine_data = [{"data_type":"Number","operator":">","question_id":int(self.question.id),"value": str(split_text[1])}]
                except:
                    pass
        return rule_engine_data


    def __str__(self):
        #                                                          choice
        # sets name as unicode
        try:
            return "%s || %s || %s" % (self.question.block.survey, self.question, self.text)
        except:
            return "%s || %s || %s" % (self.question.block.survey, self.question.id, self.text)

    class Meta:
        # Don't create a table in database
        # This table is abstract
        ordering = ('question', 'choice_order')


class JsonAnswer(BaseContent):
    INTERFACE_TYPES = (('0', 'Web'),('1', 'App'),('2', 'Migrated Data'))
    user = models.ForeignKey(User, related_name='jsonanswers',
                             verbose_name=_('jsonuser'),
                             blank=True, null=True,on_delete=models.DO_NOTHING,)
    creation_key = models.CharField(max_length=75, unique=True)
    submission_date = models.DateTimeField(auto_now=True)
    survey = models.ForeignKey(Survey, blank=True, null=True,on_delete=models.DO_NOTHING)
    app_answer_on = models.DateTimeField(blank=True, null=True)
    app_answer_data = models.PositiveIntegerField(blank=True, null=True)
    response = models.JSONField(default=dict)
    cluster = models.JSONField(default=dict)
    interface = models.CharField(choices=INTERFACE_TYPES,default=1,max_length=2)
    language = models.ForeignKey('survey.Language', blank=True, null=True,on_delete=models.DO_NOTHING)
    # beneficiary_type = models.ForeignKey('beneficiary.BeneficiaryType', blank=True, null=True,on_delete=models.DO_NOTHING)
    training_type = models.ForeignKey('application_master.MasterLookUp', blank=True, null=True,on_delete=models.DO_NOTHING)
    json_order = models.PositiveIntegerField(blank=True,null=True)
    training_survey = models.ForeignKey(Survey, blank=True, null=True,related_name='training_survey',on_delete=models.DO_NOTHING)
    inner_response_creation_key = models.CharField(max_length=50, blank=True,null=True)
    lead_user = models.ForeignKey(User, related_name='leadusers',
                             verbose_name=_('leadusers'),
                             blank=True, null=True,on_delete=models.DO_NOTHING)

    #facilty id for storing the facility of response
    facility_id = models.IntegerField(blank=True,null=True,default=0,db_index = True)


    searching=['id','facility_id','creation_key']
    class Meta:
        indexes = [
            models.Index(fields=['survey_id', 'user_id']),
        ]

    def __str__(self):
        # Unicode for answer
        return str(self.survey) + '__' + str(self.user) + '__' + str(self.id)
    
    #TODO: Not used in subhiksha application
    def get_followup_sts(self):
        fp = JsonAnswer.objects.get(survey=112,creation_key=self.creation_key)
        if fp.response.get('883')=='1850':
            sts = True
        else:
            sts = False
        return sts

    # def get_beneficiary_object(self):
    #     obj = None
    #     try:
    #         from beneficiary.models import BeneficiaryResponse
    #         obj = BeneficiaryResponse.objects.get(json_answer_id=self.id)
    #     except:
    #         pass
    #     return obj

    #TODO: Not used in subhiksha application
    def get_response_location(self):
        location_id = 0
        if self.survey.survey_type == 1:
            location_id = self.cluster.get('Boundary') if self.cluster.get('Boundary') != "None" else 0
        return location_id

    #TODO: Not used in subhiksha application
    # def get_response_details(self):
    #     ben_name, boundary_name = '', ''
    #     if self.cluster.get('BeneficiaryResponse'):
    #         from beneficiary.models import BeneficiaryResponse
    #         ben_name = BeneficiaryResponse.objects.get(creation_key=self.cluster.get('BeneficiaryResponse')).get_response_name()
    #     if self.get_response_location():
    #         boundary_name = Boundary.objects.get(id=self.get_response_location()).name
    #     return str(ben_name) + '(' + str(boundary_name) + ')'

    # #TODO: Not used in subhiksha application
    # def get_response_name(self):
    #     # from userroles.serializers import user_setup
    #     code_concate = user_setup().get('user_display_code',0)
    #     try:
    #         question = self.survey.questions().filter(display_has_name=True)[0]
    #     except:
    #         question = self.survey.questions().filter(qtype__in=['T', 'S', 'R'], parent=None)[0]
    #     disp_name = self.response.get(str(question.id))
    #     if self.survey.questions().filter(training_config__has_key="with_code_question") and code_concate:
    #         que =self.survey.questions().filter(training_config__has_key="with_code_question")[0]
    #         code_value=self.response.get(str(que.training_config["with_code_question"]["q_id"]))
    #         disp_name ="{} ({})".format(disp_name,code_value)
    #     return disp_name

    #TODO: Not used in anywhere
    def get_aad(self):
        return AppAnswerData.objects.get(id=self.app_answer_data)

    def get_partner(self):
        try:
            partner_id = UserRoles.objects.get(user=self.user).partner.id
        except:
            partner_id  = None
        return partner_id

    # def get_beneficiary(self):
    #     bene_type = bene_id = loc_id = 0
    #     get_response = self.cluster.get('beneficiary', 0) or 0
    #     if get_response:
    #         bene_type, bene_id = get_response.get(
    #             'beneficiary_type_id', 0), get_response.get('id', 0)
    #         if bene_type and bene_id:
    #             try:
    #                 loc = Beneficiary.objects.get(id=bene_id)
    #                 new_dict = literal_eval(loc.jsondata['address'][0])
    #                 loc_id = int(new_dict.values()[0].get(
    #                     'boundary_id', 0) or 0)
    #             except:
    #                 pass
    #     return bene_type, bene_id, loc_id

    #TODO: Not used in subhiksha application
    def get_response_files_object(self):
        try:
            rf = ResponseFiles.objects.get_or_none(content_type=ContentType.objects.get_for_model(self), object_id=self.id)
        except:
            rf = None
        return rf

    #TODO: Not used in subhiksha application
    def convert_into_object(self, data_json):
        try:
            data = literal_eval(data_json)
        except:
            data = data_json
        return data
    
    #TODO: Not used in subhiksha application
    def get_image_info(self):
        img_info = []
        try:
            img_info = Media.objects.filter(app_answer_data=self.app_answer_data,active=2)
            if img_info:
                img_info = [{"qid":i.question.id,"unique_id":i.unqid,"capture_time":i.app_answer_on.strftime('%Y-%m-%d %I:%M:%s')
,"path":i.image.url} for i in img_info]
            else:
                img_info = []
        except:
            img_info = []
        return img_info

def get_parent_obj(answer,child_obj):
    try:
        queryset = 'child_obj.' + ('parent.' * answer) + 'id'
        parent_obj_id = eval(queryset)
    except:
        parent_obj_id = child_obj.id
    return parent_obj_id

def get_parent_query(child_level_id,parent_level_id,boundary_child_id):

    normal_format = 'parent__'
    query_dict = {}
    boundary_child_ids = []
    child_query_dict = {}
    answer = child_level_id - parent_level_id if child_level_id > parent_level_id else parent_level_id-child_level_id
    query = normal_format * int(answer) + 'id' if answer > 0 else normal_format + 'id'
    query_dict[query] = boundary_child_id
    child_obj = Boundary.objects.get_or_none(id = boundary_child_id)
    if child_obj:
        parent_obj_id = get_parent_obj(answer,child_obj)
        parent_obj = Boundary.objects.get_or_none(id = parent_obj_id)
        child_query_dict[query] = parent_obj_id
        boundary_child_ids = list(set(Boundary.objects.filter(**child_query_dict).values_list("id",flat=True)))
    return parent_obj,boundary_child_ids

def get_user_role(user):
    roleobj = UserRoles.objects.get_or_none(user = user)
    if roleobj:
        roles = roleobj.role_type.all().values_list("slug",flat=True)
    else:
        roles = []
    return roles

# def get_survey_periodicity(survey_workflow):
#     # from userroles.serializers import user_setup
#     periodicity_way = user_setup().get('periodicity_as_survey',2)
#     periodicity = 0
#     if periodicity_way == 0 and survey_workflow:
# #        0 is false so periodicity will be taken from workflow
#         periodicity = survey_workflow.periodicity
#     elif periodicity_way == 2 and survey_workflow:
# #        2 is true,so periodicity will be taken from survey 
#         periodicity = survey_workflow.survey.periodicity
#     return periodicity

class Media(BaseContent):
   user = models.ForeignKey(User, related_name='media', verbose_name=_('user'),
                            blank=True, null=True,on_delete=models.DO_NOTHING)
   question = models.ForeignKey(Question, related_name='media',
                                verbose_name=_('question'),on_delete=models.DO_NOTHING)
   submission_date = models.DateTimeField(auto_now=True)
   content_type = models.ForeignKey(ContentType,on_delete=models.DO_NOTHING)
   object_id = models.PositiveIntegerField()
   image = models.ImageField(
       upload_to='static/%Y/%m/%d', blank=True, null=True)
   sfile = models.FileField(
       upload_to='static/surveyfiles/%Y/%m/%d', blank=True, null=True)
   app_answer_on = models.DateTimeField(blank=True, null=True)
   app_answer_data = models.CharField(max_length=255, blank=True, null=True)
   unqid = models.CharField(max_length=255, blank=True, null=True)

   def __str__(self):
       return '%s - %s' % (self.id, self.object_id)

class SurveyDisplayQuestions(BaseContent):
    survey = models.ForeignKey(Survey,on_delete=models.DO_NOTHING)
    display_type = models.CharField(max_length=100,
                                    choices=DISPLAY_TYPE_CHOICES)
    questions = models.JSONField(default=dict)

    def __str__(self):
        # Unicode for answer
        return str(self.survey)



class ErrorLog(BaseContent):
    user = models.ForeignKey(User,on_delete=models.DO_NOTHING)
    stoken = models.CharField(max_length=255, blank=True, null=True)
    log_file = models.FileField(
        upload_to='media/logfiles/%Y/%m/%d', blank=True, null=True)

    def __str__(self):
        return str(self.id)



class Language(BaseContent):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True, null=True)
    help_text = models.CharField(max_length=255, blank=True, null=True)
    char_field1 = models.CharField(max_length=500, blank=True, null=True)
    char_field2 = models.CharField(max_length=500, blank=True, null=True)
    integer_field1 = models.IntegerField(default=0)
    integer_field2 = models.IntegerField(default=0)
    # states = models.ManyToManyField(Boundary)

    def __str__(self):
        return self.name



class AppLoginDetails(BaseContent):
    user = models.ForeignKey(User,on_delete=models.DO_NOTHING)
    surveyversion = models.CharField(max_length=10, blank=True, null=True)
    lang_code = models.CharField(max_length=10, blank=True, null=True)
    tabtime = models.DateTimeField(blank=True, null=True)
    sdc = models.PositiveIntegerField(default=0)
    itype = models.CharField(max_length=10, blank=True, null=True)
    version_number = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.user.username


class AppAnswerData(BaseContent):
    interface = models.IntegerField(default=0, choices=(
        (0, 'Web'), (2, 'Android App'),
    ))
    latitude = models.CharField(max_length=255, blank=True, null=True)
    longitude = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    version_number = models.CharField(max_length=10, blank=True, null=True)
    app_version = models.CharField(max_length=10, blank=True, null=True)
    language_id = models.CharField(max_length=10, blank=True, null=True)
    imei = models.CharField(max_length=100, blank=True, null=True)
    survey_id = models.CharField(max_length=50, blank=True, null=True)
    mode = models.CharField(max_length=50, blank=True, null=True)
    part2_charge = models.CharField(max_length=50, blank=True, null=True)
    f_sy = models.CharField(max_length=50, blank=True, null=True)
    gps_tracker = models.CharField(max_length=10, blank=True, null=True)
    survey_status = models.CharField(max_length=50, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    sp_s_o = models.DateTimeField(blank=True, null=True)
    reason = models.CharField(max_length=255, blank=True, null=True)
    cluster_id = models.CharField(max_length=50, blank=True, null=True)
    cell_id = models.CharField(max_length=100, blank=True, null=True)
    signal_strength = models.CharField(max_length=50, blank=True, null=True)
    lac = models.CharField(max_length=50, blank=True, null=True)
    mcc = models.CharField(max_length=50, blank=True, null=True)
    mnc = models.CharField(max_length=50, blank=True, null=True)
    la = models.CharField(max_length=50, blank=True, null=True)
    carrier = models.CharField(max_length=50, blank=True, null=True)
    network_type = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    chargeleft = models.CharField(max_length=20, blank=True, null=True)
    charge_connected = models.CharField(max_length=50, blank=True, null=True)
    last_chargetime = models.CharField(max_length=50, blank=True, null=True)
    sim_serialnumber = models.CharField(max_length=100, blank=True, null=True)
    device_id = models.CharField(max_length=100, blank=True, null=True)
    is_cus_rom = models.CharField(max_length=50, blank=True, null=True)
    pe_r = models.CharField(max_length=50, blank=True, null=True)
    ospr = models.CharField(max_length=50, blank=True, null=True)
    lqc = models.CharField(max_length=50, blank=True, null=True)
    sdc = models.CharField(max_length=50, blank=True, null=True)
    dom_id = models.CharField(max_length=50, blank=True, null=True)
    survey_part = models.CharField(max_length=50, blank=True, null=True)
    c_status = models.CharField(max_length=50, blank=True, null=True)
    stoken_sent = models.CharField(max_length=255, blank=True, null=True)
    sample_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.PositiveIntegerField(default=0, choices=(
        (0, '------'), (1, 'Valid'), (2, 'Invalid'),
    ))
    description = models.TextField(null=True)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return str(self.id)

class DeviceDetails(BaseContent):
    user = models.ForeignKey(User,on_delete=models.DO_NOTHING)
    submission_date = models.DateTimeField(auto_now=True)
    app_size = models.CharField(max_length=20, blank=True, null=True)
    disk_free_space = models.CharField(max_length=20, blank=True, null=True)
    primary_storage = models.CharField(max_length=20, blank=True, null=True)
    secondary_storage = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return self.user.username

class Version(BaseContent):
    survey = models.ForeignKey(Survey,on_delete=models.DO_NOTHING)
    version_number = models.CharField(max_length=255, blank=True, null=True)
    create_by = models.ForeignKey(User, blank=True, null=True,on_delete=models.DO_NOTHING)
    changes = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.ForeignKey(ContentType,on_delete=models.DO_NOTHING)
    object_id = models.PositiveIntegerField()

    def __str__(self):
        return '%s || %s || %s' % (self.survey, self.version_number, self.changes)

    def get_action(self, **kwargs):
        status = ''
        obj = kwargs.get('obj')
        if float(self.version_number) == 0.0:
            status = 'C'
        elif float(self.version_number) >= 0.1 and obj:
            model_name = obj.__class__.__name__.lower()
            version_list = Version.objects.filter(survey=self.survey)
            vs_list = version_list.filter(content_type__model__iexact=model_name,
                                          object_id=int(obj.id)).order_by('-id')
            if len(vs_list) >= 1:
                status = vs_list[0].action
            else:
                status = 'C'
        return status


class SurveySkip(BaseContent):
    survey = models.ForeignKey(Survey,on_delete=models.DO_NOTHING, related_name='survey')
    skipto_survey = models.ForeignKey(
        Survey,on_delete=models.DO_NOTHING, blank=True, null=True, related_name='skipto_survey')
    question = models.ForeignKey(Question,on_delete=models.DO_NOTHING, blank=True, null=True)
    skip_level = models.CharField(max_length=255, blank=True, null=True)


class Validations(BaseContent):
    validation_type = models.CharField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.validation_type



class QuestionValidation(BaseContent):
    question = models.ForeignKey(Question,on_delete=models.DO_NOTHING)
    validationtype = models.ForeignKey(Validations, blank=True, null=True,on_delete=models.DO_NOTHING)
    max_value = models.CharField(max_length=100, blank=True, null=True)
    min_value = models.CharField(max_length=100, blank=True, null=True)
    message = models.CharField(max_length=255, blank=True, null=True)

    def clean(self):
        if self.max_value and self.min_value and (float(self.min_value) or 0) > (float(self.max_value) or float('inf')):
            raise ValidationError({
                'min_value': 'Min value should be less than max value',
            })

    def __str__(self):
        return self.question.text


class SurveyLog(BaseContent):
    create_by = models.ForeignKey(User,on_delete=models.DO_NOTHING)
    log_value = models.CharField(max_length=255, blank=True, null=True)
    version = models.ForeignKey(Version,on_delete=models.DO_NOTHING)
    other_text = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.create_by.username


class AppLabel(BaseContent):
    name = models.CharField(max_length=255)
    help_text = models.CharField(max_length=255, blank=True, null=True)
    other_text = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class QuestionLanguageValidation(BaseContent):
    questionvalidation = models.ForeignKey(QuestionValidation,on_delete=models.DO_NOTHING)
    language = models.ForeignKey(Language,on_delete=models.DO_NOTHING)
    text = models.CharField(max_length=255)
    other_text = models.CharField(max_length=255, blank=True, null=True)



class Levels(BaseContent):
    name = models.CharField(max_length=255, blank=True, null=True)
    survey = models.ForeignKey(Survey,on_delete=models.DO_NOTHING)
    content_type = models.ForeignKey(ContentType,on_delete=models.DO_NOTHING)
    level_order = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name


class ProjectLevels(BaseContent):
    name = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.ForeignKey(ContentType,on_delete=models.DO_NOTHING)
    projectlevel_order = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name


class VersionUpdate(BaseContent):
    version_code = models.IntegerField(default=0)
    version_name = models.CharField(max_length=100, blank=True, null=True)
    force_update = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.version_code)


# pass question list to filter according upto skip question
def get_filter_skip_question(question_list):
    last_question = question_list.last()
    for i in question_list:
        if i.is_skip_question():
            last_question = i
            break
    return {'first': question_list.first(), 'last': last_question}


def make_dir(instance, filename):
    d_ = datetime.now().date()
    year, month, day = d_.year, d_.month, d_.day
    path_ = 'static/survey_dump_files/'
    path_file = path_ + '{0}/{1}/{2}/{3}'.format(year, month, day, filename)
    return path_file


class ResponseFiles(BaseContent):
    response_image = models.FileField(
        upload_to='static/%Y/%m/%d', blank=True, null=True)
    question = models.ForeignKey(Question, blank=True, null=True,on_delete=models.DO_NOTHING)
    content_type = models.ForeignKey(ContentType, blank=True, null=True,on_delete=models.DO_NOTHING)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    creation_key = models.CharField('UUID', max_length=100, blank=True,null=True)
    approve = models.BooleanField(default=False)
    reject = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class LanguageTranslationText(BaseContent):
    content_type = models.ForeignKey(ContentType, blank=True, null=True,on_delete=models.DO_NOTHING)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    language = models.ForeignKey(Language,on_delete=models.DO_NOTHING)
    text = models.CharField(max_length=500, blank=True, null=True)
    message = models.CharField(max_length=500, blank=True, null=True)
    help_text = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        unique_together = (('content_type', 'object_id', 'language'),)


class LabelLanguageTranslation(BaseContent):
    applabel = models.ForeignKey(AppLabel,on_delete=models.DO_NOTHING)
    text = models.CharField(max_length=255)
    language = models.ForeignKey(Language,on_delete=models.DO_NOTHING)
    other_text = models.CharField(max_length=255, blank=True, null=True)
    integer_field = models.IntegerField(default=0)

######################## Beneficiary Models ################
class BeneficiaryType(BaseContent):
    name = models.CharField('Name', max_length=100)
    parent = models.ForeignKey('self',on_delete=models.DO_NOTHING, blank=True, null=True)
    is_main = models.BooleanField(default=False)
    btype_order = models.IntegerField(null=True, blank=True)
    allow_multiple_address = models.BooleanField(default=False)
    color = models.CharField('Color', max_length=50, blank=True, null=True)
    is_training_type = models.BooleanField(default=False)
    is_admin_type = models.BooleanField(default=False)
    is_training_module = models.BooleanField(default=False)
    category = models.ForeignKey(MasterLookUp, on_delete=models.DO_NOTHING, \
                blank=True, null=True)
    is_activist_group = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_childs(self):
        return BeneficiaryType.objects.filter(parent=self, active=2).order_by('btype_order')

    def get_survey(self):
        """ Survey object of Beneficiary Type """
        survey = Survey.objects.get_or_none(survey_type=0, content_type=\
                        ContentType.objects.get_for_model(self), object_id=self.id)
        return survey

    def get_answers_count(self):
        """ Returns the count of answers for this beneficiary type"""
        if self.get_survey() and self.get_survey().survey_type == 0:
            answers = BeneficiaryResponse.objects.filter(survey=self.get_survey())
        else:
            answers = JsonAnswer.objects.filter(survey=self.get_survey())
        return answers.count()

    def get_answers(self):
        """ Returns the answers for this beneficiary type"""
        if self.get_survey() and self.get_survey().survey_type == 0:
            answers = BeneficiaryResponse.objects.filter(
                survey=self.get_survey())
        else:
            answers = JsonAnswer.objects.filter(survey=self.get_survey())
        return answers


class BeneficiaryResponse(BaseContent):
    survey = models.ForeignKey('survey.Survey', on_delete=models.DO_NOTHING, \
                blank=True, null=True)
    beneficiary_type = models.ForeignKey(
        BeneficiaryType, blank=True, null=True,on_delete=models.DO_NOTHING)
    partner = models.ForeignKey(
        'application_master.Partner', blank=True, null=True, related_name='beneficiary_partner',on_delete=models.DO_NOTHING)
    creation_key = models.CharField('UUID', max_length=100, unique=True)
    list_view = models.JSONField(default=dict)
    profile_view = models.JSONField(default=dict)
    json_answer_id = models.IntegerField(default=0)
    code = models.CharField(max_length=50, blank=True, null=True)
    parent_beneficiary = models.IntegerField(blank=True, null=True)
    address_1 = models.IntegerField(default=0)
    address_2 = models.IntegerField(default=0)
    address_3 = models.IntegerField(default=0)
    address_4 = models.IntegerField(default=0)
    address_5 = models.IntegerField(default=0, db_index=True)
    address_6 = models.IntegerField(default=0)
    address_7 = models.IntegerField(default=0)
    address_8 = models.IntegerField(default=0)
    duplicate_status = models.IntegerField(null=True,blank=True,choices=((1,'Approved'),(2,'Duplicate'),(3,'Rejected')))
    duplicate_marked_date = models.DateTimeField(blank=True,null=True)
    duplicate_marked_by = models.ForeignKey(User,on_delete=models.DO_NOTHING,blank=True,null=True)
    
    # Beneficciary workflow 
    approval_status = models.IntegerField(default=1,null=True,blank=True,choices=((0,'Submitted for approval'),(1,'Draft'),(2,'Approved'),(3,'Rejected')))
    approved_by = models.ForeignKey(User, related_name="approved_by_users",on_delete=models.DO_NOTHING,blank=True,null=True)
    approved_on = models.DateTimeField(blank=True,null=True)

    def __str__(self):
        # Unicode for answer
        return str(self.survey) + '-' + str(self.get_response_name())

    def response(self):
        return JsonAnswer.objects.get(id=self.json_answer_id).response

    def get_cluster(self):
        return JsonAnswer.objects.get(id=self.json_answer_id).cluster

    def get_answer(self):
        try:
            answer = JsonAnswer.objects.get(id=self.json_answer_id)
        except:
            answer = None
        return answer

    def get_response_name(self):
        disp_name = ''
        code_concate = user_setup().get('user_display_code',0)
        try:
            question = self.survey.questions().filter(display_has_name=True)[0]
        except:
            try:
                question = self.survey.questions().filter(qtype__in=['T', 'S'])[0]
            except:
                question = self.survey.get_form_questions().filter(qtype__in=['T','S'])[0] if self.survey.get_form_questions() else None
        if question:
            disp_name = self.response().get(str(question.id))
            if self.survey.questions().filter(training_config__has_key="with_code_question") and code_concate:
                que =self.survey.questions().filter(training_config__has_key="with_code_question")[0]
                code_value=self.response().get(str(que.training_config["with_code_question"]["q_id"]))
                disp_name ="{} - {}".format(disp_name,code_value)
        return disp_name

    def get_beneficiary_address(self):
        try:
            answer = JsonAnswer.objects.get(id=self.json_answer_id)
            if answer.survey.is_beneficiary_based_child() == False:
                qid = answer.survey.questions().filter(qtype='AW')[0].id
            else:
                qid = answer.survey.get_parent_beneficiary_address().id
            from configuration_settings.form_views import get_survey_based_location
            least_level = get_survey_based_location(answer.survey)
            if answer.survey.extra_config.get('least_location_level_config'):
                least_level = answer.survey.extra_config.get('least_location_level_config')
            location = answer.response.get('address').get('1').get(str(qid)).get(str(least_level))
        except:
            location = None
        return location

    def get_location_name(self):
        location_name = ''
        try:
            if self.get_beneficiary_address():
                location_name = Boundary.objects.get(id=self.get_beneficiary_address()).name
        except:
            pass
        return location_name

    def get_location_object(self):
        location_name = ''
        if self.get_beneficiary_address():
            location_name = Boundary.objects.get(id=self.get_beneficiary_address())
        return location_name
        
    def get_benefited_address(self):
        try:
            answer = JsonAnswer.objects.get(id=self.json_answer_id)
            location = answer.response.get('address')
        except:
            location = []
        return location