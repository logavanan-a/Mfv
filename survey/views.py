from django.shortcuts import render
from django.views.generic import View
from survey.models import *
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.conf import settings
from .forms import *
from rest_framework.generics import (CreateAPIView)
from survey.serializers import LinkageListingSerializer
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import pandas as pd
from django.shortcuts import render,HttpResponse,HttpResponseRedirect
import bleach,os
from rest_framework.response import Response
from cache_configuration.views import load_data_to_cache_survey,load_data_to_cache_questions,load_data_to_cache_boundary_level,cache_delete_namespace
from django.contrib import messages
from survey.management.commands.import_responses import questions_validation
from io import BytesIO
import subprocess
import logging
from rest_framework.views import APIView
from django.utils import timezone
from application_master.views import record_deactivate
from collections import defaultdict
from django.db.models import Q

logger = logging.getLogger(__name__)


pg_size = settings.REST_FRAMEWORK.get('PAGE_SIZE')

# Create your views here.
def get_pagination(request,users):
    paginator = Paginator(users, pg_size) # Show no of object per page
    page = request.GET.get('page',1)
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    return users


def import_questions(path):
    qtype_dict = {'Type In': 'T', 'Radiobutton': 'R', 'Checkbox': 'C', 'Dropdown': 'S', \
        'Date': 'D', 'Grid' :'GD', 'Inline': 'In', 'AI': 'AI', 'Address': 'AW'}

    # Load Excel file into a DataFrame
    df = pd.read_excel(path)
    # df.dropna(inplace=True)
    df.fillna("", inplace=True)
    for index, row in df.iterrows():
        survey_obj, block_obj, question_obj = None, None, None

        survey_name = str(row[0]).strip()
        block_code = str(row[1]).strip()
        block_name = str(row[2]).strip()
        question_code = str(row[4]).strip()
        parent_question = str(row[5]).strip()
        address_question = str(row[6]).strip()
        row_question = str(row[7]).strip()
        question_name = str(row[8]).strip()
        question_helptext = str(row[9]).strip()
        question_type = str(row[10]).strip()
        question_mandatory = str(row[11]).strip()
        question_min_value = str(row[12]).strip()
        question_max_value = str(row[13]).strip()
        question_error_message = str(row[14]).strip()
        question_validation_type = str(row[15]).strip()
        choice_question_code = str(row[16]).strip()
        choice_order = str(row[17]).strip()
        display_questions = str(row[18]).strip()
        choice_name = str(row[19]).strip()

        # print (survey_name ,choice_name ,parent_question, "\n" )
        if survey_name:
            # print(survey_name,'survey_name')
            survey_obj = Survey.objects.get(name=survey_name,active=2)
            block_obj,created = Block.objects.get_or_create(survey=survey_obj,code=int(eval(block_code)),active=2)
            block_obj.name=block_name
            block_obj.save()
        if survey_obj and question_code:
            question_obj, created = Question.objects.get_or_create(code=int(literal_eval(question_code)), block=block_obj)
            question_obj.text = question_name
            question_obj.question_order = int(literal_eval(question_code))
            question_obj.qtype = qtype_dict.get(question_type, 'T')
            question_obj.help_text = question_helptext
            if question_mandatory and int(literal_eval(question_mandatory)) == 2:
                question_obj.mandatory = True
            else:
                question_obj.mandatory = False
            if address_question and int(literal_eval(address_question)) == 2:
                question_obj.address_question = True
            if row_question and int(literal_eval(row_question)) == 2:
                question_obj.is_grid = True
            if parent_question:
                parent_question_object = Question.objects.get_or_none(code=int(literal_eval(parent_question)), block__survey=survey_obj)
                question_obj.parent = parent_question_object
            question_obj.save()
            if question_min_value or question_max_value or question_error_message or question_validation_type:
                question_validation_object, created = QuestionValidation.objects.get_or_create(question=question_obj)
                if question_max_value:
                    question_validation_object.max_value = int(literal_eval(question_max_value))
                if question_min_value:
                    question_validation_object.min_value = int(literal_eval(question_min_value))
                question_validation_object.message = question_error_message
                if question_validation_type:
                    validation_object = Validations.objects.get_or_none(code=question_validation_type)
                    question_validation_object.validationtype = validation_object
                question_validation_object.save()
    for index, row in df.iterrows():
        survey_obj, choice_question_obj, question_obj = None, None, None
        survey_name = str(row[0]).strip()
        block_code = str(row[1]).strip()
        block_name = str(row[2]).strip()
        question_code = str(row[4]).strip()
        parent_question = str(row[5]).strip()
        address_question = str(row[6]).strip()
        question_name = str(row[8]).strip()
        question_helptext = str(row[9]).strip()
        question_type = str(row[10]).strip()
        question_mandatory = str(row[11]).strip()
        question_min_value = str(row[12]).strip()
        question_max_value = str(row[13]).strip()
        question_error_message = str(row[14]).strip()
        question_validation_type = str(row[15]).strip()
        choice_question_code = str(row[16]).strip()
        choice_order = str(row[17]).strip()
        display_questions = str(row[18]).strip()
        # choice_name = str(row[19]).strip()
        choice_name = str(row[19]).strip() if str(row[19]).strip() != float else int(row[19]).strip()
        if survey_name:
            survey_obj = Survey.objects.get(name=survey_name,active=2)
            block_obj = Block.objects.get(survey=survey_obj,code=eval(block_code),active=2)
        if survey_obj and choice_question_code:
            choice_question_obj = Question.objects.get(code=int(literal_eval(choice_question_code)), block__survey=survey_obj)
            if choice_order:
                choice_object, created = Choice.objects.get_or_create(code=int(literal_eval(choice_order)), question=choice_question_obj)
                choice_object.text = choice_name
                if choice_order:
                    choice_object.choice_order = int(literal_eval(choice_order))
                if display_questions:
                    questions_code_list = map(int, map(float, display_questions.split(',')))
                    questions = Question.objects.filter(code__in=questions_code_list, block__survey=survey_obj)
                    for question in questions:
                        choice_object.skip_question.add(question)
                choice_object.save()


def import_modified_questions(path):
    try:
        df = pd.read_csv(path)  # Load CSV file into pandas DataFrame
        df.fillna("", inplace=True)
        # Assuming the CSV file has columns: id, question_order, code, code_display, text
        for index, row in df.iterrows():
            que = Question.objects.get(id=row['id'])
            que.question_order = row['question_order']
            que.code = row['code']
            que.code_display = row['code_display']
            que.text = row['text']
            que.save()
            print(que.text, que.question_order, que.code, que.code_display)

    except Exception as e:
        print(e.args[0])


@method_decorator(login_required, name='dispatch')
class Surveys(View):
    template_name = 'survey_forms/survey_list.html'
    
    def get(self, request, *args, **kwargs):
        # anonymous_user_entry = user_setup().get('anonymous_user_entry')
        heading="Data collections"
        surveys = Survey.objects.filter().exclude(active=0).order_by("survey_order")
        search_txt = request.GET.get('s')
        if search_txt:
            surveys = surveys.filter(name__icontains = search_txt)
        object_list = get_pagination(request, surveys)
        
        # mission name dictionary with beneficiary
        beneficiary_to_mission = dict(BeneficiaryType.objects.filter(active=2).values_list('id','category__name'))
        activity_beneficiary_dict = {}
        for i in surveys :
            activity_beneficiary_dict[i.id] = i.object_id or int(i.config[0].get('object_id_1',0))

        return render(request,self.template_name,locals())
    
# def user_setup():
#     config,created = ConfigOption.objects.get_or_create(code=0)
#     user_setup = config.jsondata
#     return user_setup

def sanitized(val):
    if val:
        return bleach.clean(val, settings.BLEACH_VALID_TAGS, settings.BLEACH_VALID_ATTRS, settings.BLEACH_VALID_STYLES)
    else:
        return ''


class SurveyAdd(View):
    template_name = 'survey_forms/survey_add.html'
    def get(self, request, *args, **kwargs):
        add = True
        survey_type_choices = SURVEY_TYPE_CHOICES
        periodicity_choices = PERIODICITY_CHOICES
        capture_level_choices= CAPTURE_LEVEL_CHOICES
        # """#survey_order=Survey.objects.get('survey_order')"""
        themes = MasterLookUp.objects.filter(parent__slug="theme")
        
        beneficiary_types = BeneficiaryType.objects.filter(active=2).exclude(parent=None).order_by('btype_order')
        beneficiary_types_ben = beneficiary_types.exclude(id__in=Survey.objects.filter(active=2,survey_type=0).values_list('object_id')).exclude(parent=None).values('id','name','category_id')
        beneficiary_type_mission = defaultdict(list)
        for i in beneficiary_types_ben:
            beneficiary_type_mission[i['category_id']].append(i['id'])
        beneficiary_type_mission = dict(beneficiary_type_mission)

        levels = BoundaryLevel.objects.all()
        missions = Mission.objects.filter(active=2)
        return render(request,self.template_name,locals())
    
    def post(self, request,*args, **kwargs):
        add = True
        # roles = RoleTypes.objects.filter(active=2)
        survey_type_choices = SURVEY_TYPE_CHOICES
        periodicity_choices = PERIODICITY_CHOICES
        capture_level_choices= CAPTURE_LEVEL_CHOICES
        beneficiary_types = BeneficiaryType.objects.filter(active=2).exclude(parent=None).order_by('btype_order')
        levels = BoundaryLevel.objects.all()
        name = sanitized(request.POST.get('name'))
        beneficiary_type_id = request.POST.get('beneficiary_type_id')
        location_id = request.POST.get('level_id')
        survey_type = request.POST.get('survey_type')
        periodicity = request.POST.get('periodicity')
        role_type = request.POST.get('role_id')
        description = request.POST.get('description')
        activity_code = request.POST.get('activity_code')
        survey_order=request.POST.get('survey_order') #if request.POST.get('survey_order') else 0
        data_dict = {}
        if Survey.objects.filter(survey_order=request.POST.get('survey_order')).exists():
             error="survey order is already exists" 
             return render(request,self.template_name,locals())
        
            
        if survey_type:
            
            if str(survey_type) == str(0):
                if Survey.objects.filter(content_type=ContentType.objects.get_for_model(BeneficiaryType), object_id=beneficiary_type_id):
                    error = "Baseline activity with this beneficiary type already exists"
                    return render(request,self.template_name,locals())
#              """  #if Survey.objects.filter(survey_order=request.POST.get('surevy_order')).exists():
#                #   error="survey order is already exists"
#                #  return render(request,self.template_name,locals())"""
                else:
                    data_dict = add_baseline_survey(data_dict,request.POST)
                    survey_object = Survey.objects.create(**data_dict)
                    Block.objects.create(block_order=1, code=1, name=name, survey=survey_object)
                    
                    
            elif str(survey_type) == str(1):
                data_dict = add_extended_survey(data_dict, request.POST)
                survey_object = Survey.objects.create(**data_dict)
                Block.objects.create(block_order=1, code=1, name=name, survey=survey_object)
            '''
                ###############################################################################
                * Below if condition is because of anonymous user entry for forms
                * 8 digits hashcode will be generated based on survey slug
                * Fields --> hashcode, anonymous_user_entry,data will be dictionary 
                * which helps to display extra information in html
                * These fields will be saved in extra_config column of survey object
                ###############################################################################
                
            '''
            # if user_setup().get('anonymous_user_entry') == 1:
            #     data_ = {"hash_code":int(str(abs(hash(survey_object.slug)))[:8]),
            #              "anonymous_user_entry":1,
            #              "data":{}
            #             }
            #     survey_object.extra_config = data_
            #     survey_object.save()
            ''' *********************Anonymous user ENDS HERE********************* '''
            cache_delete_namespace('FORM_BUILDER')
            return HttpResponseRedirect('/survey/')
        else:
            error = "Please select survey type"
        return render(request,self.template_name,locals())

#sub function for add activity if type is baseline
def add_baseline_survey(data_dict,data ):
    name = sanitized(data.get('name'))
    beneficiary_type_id = data.get('beneficiary_type_id') 
    location_id = data.get('level_id')
    survey_type = data.get('survey_type')
    description = data.get('description')
    periodicity = data.get('periodicity')
    survey_order=data.get('survey_order')
    capture_level = data.get('cp_level')
    activity_code = data.get('activity_code')
    data_dict.update({"name": name, 
                    "survey_type": survey_type,
                    "content_type":
                		ContentType.objects.get_for_model(
                            BeneficiaryType), "object_id":
                        beneficiary_type_id, "periodicity":
                        periodicity,"survey_order":survey_order,
                        "capture_level_type":capture_level,

                        })
    return data_dict

class SurveyEdit(View):
    template_name = 'survey_forms/survey_add.html'
    def get(self, request, pk, *args, **kwargs):
        edit = True
        survey_type_choices = SURVEY_TYPE_CHOICES
        periodicity_choices = PERIODICITY_CHOICES
        survey_deactivate_reasons =  SURVEY_DEACTIVATE_REASON
        themes = MasterLookUp.objects.filter(parent__slug="theme")
        capture_level_choices= CAPTURE_LEVEL_CHOICES
        beneficiary_types = BeneficiaryType.objects.filter(active=2).exclude(parent=None).order_by('btype_order')
        levels = BoundaryLevel.objects.all()
        survey_obj = Survey.objects.get(id=pk)
        survey_order=Survey.objects.get(id=pk).survey_order
        # roles = RoleTypes.objects.filter(active=2)
        return render(request,self.template_name,locals())
    
    def post(self, request, pk, *args, **kwargs):
        add = True
        
        survey_type_choices = SURVEY_TYPE_CHOICES
        periodicity_choices = PERIODICITY_CHOICES
        capture_level_choices= CAPTURE_LEVEL_CHOICES
        # beneficiary_types = BeneficiaryType.objects.filter(active=2).exclude(parent=None).order_by('btype_order')
        levels = BoundaryLevel.objects.all()
        name = sanitized(request.POST.get('name'))
        beneficiary_type_id = request.POST.get('beneficiary_type_id')
        location_id = request.POST.get('level_id')
        survey_type = request.POST.get('survey_type')
        periodicity = request.POST.get('periodicity')
        # role_type = request.POST.get('role_id')
        survey_order=request.POST.get('survey_order') #if request.POST.get('survey_order') else 0
        data_dict = {}
        capture_level = request.POST.get('cp_level')
        if Survey.objects.filter(survey_order=request.POST.get('survey_order')).exclude(id=pk):
             error="survey order is already exists"
             return render(request,self.template_name,locals())

        if survey_type:
            survey_obj = Survey.objects.filter(id=pk)
            if str(survey_type) == str(0):
                if Survey.objects.filter(content_type=ContentType.objects.get_for_model(BeneficiaryType), \
                        object_id=beneficiary_type_id).exclude(id=pk):
                    error = "Beneficiary type already exists"
                    return render(request,self.template_name,locals())
                else:
                    data_dict.update({"name": name, 
                                  "survey_type": survey_type,
                                  "survey_order":survey_order,
                                  "content_type_id":
                                      ContentType.objects.get_for_model(
                                          BeneficiaryType).id, "object_id":
                                      beneficiary_type_id, "periodicity":
                                      periodicity,"capture_level_type":capture_level})
                    survey_obj.update(**data_dict)
            elif str(survey_type) == str(1):
                data_dict.update({"name": name,
                                  "survey_type": survey_type,
                                  "periodicity": periodicity,
                                  "survey_order":survey_order,
                                  "capture_level_type":capture_level,})
                if location_id:
                    config = [{"content_type_2": "BoundaryLevel",
                               "object_id_2": str(location_id)}]
                    data_dict.update({"config": config})
                elif beneficiary_type_id:
                    least_location_id = user_setup().get(
                        'least_location_level_config')
                    config = [{"content_type_1": "BeneficiaryType",
                               "object_id_1": str(beneficiary_type_id)},
                              {"content_type_2": "BoundaryLevel",
                               "object_id_2": str(least_location_id)}]
                    data_dict.update({"config": config})
                elif role_type:
                    location_id=OrganizationUnit.objects.get(roles=role_type).organization_level.code
                    config = [{"content_type_2": "BoundaryLevel",
                    		"object_id_2": str(location_id)},
                    		{"content_type_3": "RoleTypes",
                    		"object_id_3": str(role_type)}]
                    data_dict.update({"config": config})
                else:
                    data_dict.update({"config": {}})
                survey_obj.update(**data_dict)
            for survey_object in survey_obj:
                survey_object.save()
            return HttpResponseRedirect('/survey/')
        else:
            error = "Please select survey type"
        return render(request,self.template_name,locals())


@method_decorator(login_required, name='dispatch')
class SurveyQuestions(View):
    template_name = 'survey_forms/questions_list.html'
    
    def get(self, request, pk, *args, **kwargs):
        questions_list = Question.objects.filter(block__survey_id=pk).exclude(active=0).order_by('code')
        if self.request.GET.get('text') or request.GET.get('text'):
            txt = request.GET.get('text')
            questions_list = questions_list.filter(text__icontains=txt)
        object_list = get_pagination(request, questions_list)
        return render(request,self.template_name,locals())


@method_decorator(login_required, name='dispatch')
class AddSurveyQuestion(View):
    template_name = 'survey_forms/survey_question_add.html'
    def get(self, request, pk, parent_id='', *args, **kwargs):
        add = True
        date_validation = MasterLookUp.objects.filter(active=2,parent_id=495)
        cancel_id = pk
        form = QuestionForm()
        validations = Validations.objects.filter(active=2)
#        """#code =Validations.objects.all().order_by('-code')"""
        if parent_id:
            parent_question = Question.objects.get(id=parent_id)
        return render(request,self.template_name,locals())

    def post(self, request, pk, parent_id='', *args, **kwargs):
        add = True
        cancel_id = pk
        form = QuestionForm(request.POST)
        date_validation = MasterLookUp.objects.filter(active=2,parent_id=495) #validation date type list
        validations = Validations.objects.filter(active=2)
        survey_obj = Survey.objects.get(id=pk)
        parent_question = None
        if parent_id:
            parent_question = Question.objects.get(id=parent_id)
        block, created = Block.objects.get_or_create(survey=survey_obj, name=survey_obj.name)
        if form.is_valid():
            if Question.objects.filter(block__survey_id=pk,code=request.POST.get('code')):
                error = "Code already exists"
                return render(request,self.template_name,locals())
            qtype = request.POST.get('qtype')
            is_grid = request.POST.get('is_grid', False)
            question = form.save(commit=False)
            question.block = block
            question.parent = parent_question
            question.question_oder = request.POST.get('code')
            question.is_grid = True if is_grid == 'on' else False
            if request.POST.get('qtype') == 'AW':
                question.is_profile = True
                question.display_inline = True
                question.address_question = True
            question.save()
            if request.POST.get('qtype') == 'T' and request.POST.getlist('validation_type')[0]:
                try:
                    validationtype = Validations.objects.get_or_none(id=request.POST.getlist('validation_type')[0])
                except:
                    validationtype = None
                QuestionValidation.objects.create(question=question, \
                validationtype=validationtype, \
                min_value=request.POST.get('min_value'), max_value=request.POST.get('max_value'), \
                message=request.POST.get('message')
                )
            if request.POST.get('qtype') == 'D':
                validationtype = Validations.objects.get_or_none(id=5)
                if int(request.POST.get('validation_type')) == 496:
                    # past date
                    QuestionValidation.objects.create(question=question, \
                    validationtype=validationtype, \
                    min_value='01011900', max_value='00000000', \
                    message="Please select valid date"
                    )
                elif int(request.POST.get('validation_type')) == 497:
                    # future date
                    QuestionValidation.objects.create(question=question, \
                    validationtype=validationtype, \
                    min_value='00000000', max_value='01012050', \
                    message="Please select valid date"
                    )
                elif int(request.POST.get('validation_type')) == 498:
                    # current / today date
                    QuestionValidation.objects.create(question=question, \
                    validationtype=validationtype, \
                    min_value='00000000', max_value='00000000', \
                    message="Please select valid date"
                    )

                elif int(request.POST.get('validation_type')) == 499:
                    # All date
                    from_date=request.POST.get('from_date')
                    to_date=request.POST.get('to_date')
                    from_date_obj=datetime.datetime.strptime(from_date, '%Y-%m-%d')
                    to_date_obj=datetime.datetime.strptime(to_date, '%Y-%m-%d')
                    from_date=from_date_obj.strftime('%d%m%Y')
                    to_date=to_date_obj.strftime('%d%m%Y')

                    QuestionValidation.objects.create(question=question, \
                    validationtype=validationtype, \
                    min_value=from_date, max_value=to_date, \
                    message="Please select valid date"
                    )

                else:
                     QuestionValidation.objects.create(question=question, \
                    validationtype=validationtype, \
                    min_value='01011900', max_value='00000000', \
                    message="Please select valid date"
                    )
                question.api_json = {"date_val":request.POST.get('validation_type') if request.POST.get('validation_type') else str(496)}
                question.save()
            if qtype in ['In', 'GD']:
                return HttpResponseRedirect('/question/add/' + str(pk) + '/' + str(question.id) + '/')
            return HttpResponseRedirect('/questions/' + str(pk) + '/')
        return render(request,self.template_name,locals())
    

@method_decorator(login_required, name='dispatch')
class EditSurveyQuestion(View):
    template_name = 'survey_forms/survey_question_add.html'
    def get(self, request, pk, *args, **kwargs):
        
        edit = True
        date_validation = MasterLookUp.objects.filter(active=2,parent_id=495) # 495 : validation date type list 
        question_deactivate_reasons =  QUESTION_DEACTIVATE_REASON
        question_object = Question.objects.get(id=pk)
        try:
            question_validation = QuestionValidation.objects.get(question=question_object)
        except QuestionValidation.DoesNotExist:
            question_validation = None
        # question_validation = QuestionValidation.objects.get_or_none(question=question_object)
        if question_validation and question_object.api_json.get('date_val') == '499':
            from_date=datetime.datetime.strptime(question_validation.min_value, '%d%m%Y')
            to_date=datetime.datetime.strptime(question_validation.max_value, '%d%m%Y')

        form = QuestionForm(instance=question_object)
        validations = Validations.objects.filter(active=2)
        cancel_id = question_object.block.survey.id
        return render(request,self.template_name,locals())
    
    def post(self, request, pk, *args, **kwargs):
        edit = True
        question_object = Question.objects.get(id=pk)
        try:
            question_validation = QuestionValidation.objects.get(question=question_object)
        except QuestionValidation.DoesNotExist:
            question_validation = None
        # question_validation = QuestionValidation.objects.get_or_none(question=question_object)
        form = QuestionForm(request.POST, instance=question_object)
        validations = Validations.objects.filter(active=2)
        cancel_id = question_object.block.survey.id
        if form.is_valid():
            if Question.objects.filter(block__survey_id=question_object.block.survey_id, \
                    code=request.POST.get('code'), active=2).exclude(id=pk):
                error = "Code already exists"
                return render(request,self.template_name,locals())
            qtype = request.POST.get('qtype')
            is_grid = request.POST.get('is_grid', False)
            question = form.save(commit=False)
            question.is_grid = True if is_grid == 'on' else False
            question.question_order = request.POST.get('code')
            if question_object.qtype != 'AW':
                question.display_inline = False
                question.address_question = False
            if request.POST.get('qtype') == 'AW':
                question.is_profile = True
                question.display_inline = True
                question.address_question = True
            question.save()
            if request.POST.get('qtype') == 'T' and request.POST.getlist('validation_type')[0]:
                try:
                    validationtype = Validations.objects.get_or_none(id=request.POST.getlist('validation_type')[0])
                except:
                    validationtype = None
                validation_obj, created = QuestionValidation.objects.get_or_create(question=question_object)
                validation_obj.validationtype=validationtype
                validation_obj.min_value=request.POST.get('min_value')
                validation_obj.max_value=request.POST.get('max_value')
                validation_obj.message=request.POST.get('message')
                validation_obj.save()
            elif QuestionValidation.objects.filter(question=question_object):
                QuestionValidation.objects.filter(question=question_object).delete()
            if request.POST.get('qtype') == 'D' and request.POST.get('validation_type'):
                validationtype = Validations.objects.get_or_none(id=5)
                if int(request.POST.get('validation_type')) == 496:
                    # past date
                    QuestionValidation.objects.create(question=question, \
                    validationtype=validationtype, \
                    min_value='01011900', max_value='00000000', \
                    message="Please select valid date"
                    )
                elif int(request.POST.get('validation_type')) == 497:
                    #future date
                    QuestionValidation.objects.create(question=question, \
                    validationtype=validationtype, \
                    min_value='00000000', max_value='01012050', \
                    message="Please select valid date"
                    )
                elif int(request.POST.get('validation_type')) == 498:
                    # current / today date
                    QuestionValidation.objects.create(question=question, \
                    validationtype=validationtype, \
                    min_value='00000000', max_value='00000000', \
                    message="Please select valid date"
                    )
                    
                elif int(request.POST.get('validation_type')) == 499:
                    # all date
                    from_date=request.POST.get('from_date')
                    to_date=request.POST.get('to_date')
                    from_date_obj=datetime.datetime.strptime(from_date, '%Y-%m-%d')
                    to_date_obj=datetime.datetime.strptime(to_date, '%Y-%m-%d')
                    from_date=from_date_obj.strftime('%d%m%Y')
                    to_date=to_date_obj.strftime('%d%m%Y')

                    QuestionValidation.objects.create(question=question, \
                    validationtype=validationtype, \
                    min_value=from_date, max_value=to_date, \
                    message="Please select valid date"
                    )

                else:
                     
                     QuestionValidation.objects.create(question=question, \
                    validationtype=validationtype, \
                    min_value='01011900', max_value='00000000', \
                    message="Please select valid date"
                    )
                question.api_json = {"date_val":request.POST.get('validation_type') if request.POST.get('validation_type') else str(496)}
                question.save()
            return HttpResponseRedirect('/questions/' + str(question_object.block.survey_id) + '/')
        return render(request,self.template_name,locals())


@method_decorator(login_required, name='dispatch')
class QuestionChoices(View):
    template_name = 'survey_forms/choices_list.html'
    def get(self, request, pk, *args, **kwargs):
        choices_list = Choice.objects.filter(question_id=pk)
        question_object = Question.objects.get(id=pk)
        cancel_id = question_object.block.survey_id
        return render(request,self.template_name,locals())
    

@method_decorator(login_required, name='dispatch')
class AddQuestionChoice(View):
    template_name = 'survey_forms/question_choice_add.html'
    def get(self, request, pk, *args, **kwargs):
        add = True
        cancel_id = pk
        form = ChoiceForm()
        return render(request,self.template_name,locals())
    
    def post(self, request, pk, *args, **kwargs):
        add = True
        cancel_id = pk
        question_object = Question.objects.get(id=pk)
        form = ChoiceForm(request.POST)
        if form.is_valid():
            if Choice.objects.filter(question=question_object, code=request.POST.get('code')):
                error = "Code already exists"
                return render(request,self.template_name,locals())
            choice = form.save(commit=False)
            choice.question = question_object
            choice.choice_order = request.POST.get('code')
            choice.save()
            return HttpResponseRedirect('/choices/' + str(question_object.id) + '/')
        return render(request,self.template_name,locals())

    
@method_decorator(login_required, name='dispatch')
class EditQuestionChoice(View):
    template_name = 'survey_forms/question_choice_add.html'
    def get(self, request, pk, *args, **kwargs):
        add = False
        edit = True
        choice_deactivate_reasons =  CHOICE_DEACTIVATE_REASON
        choice_object = Choice.objects.get(id=pk)
        form = ChoiceForm(instance=choice_object)
        cancel_id = choice_object.question_id
        return render(request,self.template_name,locals())
    
    def post(self, request, pk, *args, **kwargs):
        add = False
        choice_object = Choice.objects.get(id=pk)
        form = ChoiceForm(request.POST, instance=choice_object)
        cancel_id = choice_object.question_id
        if form.is_valid():
            if Choice.objects.filter(question_id=choice_object.question.id, \
                    code=request.POST.get('code')).exclude(id=pk):
                error = "Code already exists"
                return render(request,self.template_name,locals())
            choice = form.save(commit=False)
            choice.choice_order = request.POST.get('code')
            choice.uuid = request.POST.get('uuid')
            choice.save()
            return HttpResponseRedirect('/choices/' + str(choice_object.question_id) + '/')
        return render(request,self.template_name,locals())
    

@method_decorator(login_required, name='dispatch')
class SkipQuestionChoice(View):
    template_name = 'survey_forms/skip_questions.html'
    def get(self, request, pk, *args, **kwargs):
        add = True
        question_object = Question.objects.get(id=pk)
        cancel_id = question_object.block.survey_id
        next_questions = Question.objects.filter(block__survey__id=cancel_id, code__gt=question_object.code, address_question=False, display_inline=False, active = 2 ).order_by('code')
        return render(request,self.template_name,locals())
    
    def post(self, request, pk, *args, **kwargs):
        add = True
        question_object = Question.objects.get(id=pk)
        cancel_id = question_object.block.survey_id
        keys = [k for k,v in request.POST.items() if k.startswith('choice')]
        for choice in question_object.get_choices():
            choice.skip_question.clear()
        for key in keys:
            choice = Choice.objects.get(id=key.split('_')[1])
            if request.POST.get(key):
                question = Question.objects.filter(id__in=request.POST.getlist(key))
                choice.skip_question.add(*question)
                choice.save()
        return HttpResponseRedirect('/questions/' + str(cancel_id) + '/')


@method_decorator(login_required, name='dispatch')
class ImportQuestions(View):
    template_name = 'survey_forms/add_questions_files.html'
    def get(self, request, pk):
        add = True
        return render(request,self.template_name,locals())

    def post(self, request, pk):
        add = True
        response_file_object = ResponseFiles.objects.create(response_image=request.FILES.get('file'), \
            content_type=ContentType.objects.get_for_model(Survey), \
            object_id=pk)
        file_path = str(response_file_object.response_image.path)
        import_questions(file_path)
        return HttpResponseRedirect('/manage/questions/' + str(pk) + '/')
    
class ImportMQuestions(View):
    template_name = 'survey_forms/add_questions_files.html'
    def get(self, request, pk):
        add = True
        return render(request,self.template_name,locals())

    def post(self, request, pk):
        add = True
        response_file_object = ResponseFiles.objects.create(response_image=request.FILES.get('file'), \
            content_type=ContentType.objects.get_for_model(Survey), \
            object_id=pk)
        file_path = str(response_file_object.response_image.path)
        import_modified_questions(file_path)
        return HttpResponseRedirect('/manage/questions/' + str(pk) + '/')

class ProgramRetreiveLinkages(CreateAPIView):
    serializer_class = LinkageListingSerializer
    def post(cls, request, format=None):
        # response = {'status': "success", "message": "successfully done"}
        # serializer = LinkageListingSerializer(data=request.data)
        # if serializer.is_valid():
        #     data_dict = {'content_type':ContentType.objects.get_for_model(BeneficiaryResponse),
        #         'content_type1':ContentType.objects.get_for_model(BeneficiaryResponse),
        #         'relation':None,
        #         'survey_relation':1
        #         }
        #     linkage_list,flag = get_common_linkage_details(request,data_dict)
        #     response.update({'linkages': linkage_list})
        # else:
        #     return get_serializer_errors(serializer)
        return Response({
                    "status": "success",
                    "message": "successfully done",
                    "linkages": []
                })    



@method_decorator(login_required, name='dispatch')
class SurveyResponseDataImport(View):
    template_name = 'survey_forms/survey_list_data_import.html'
    
    def get(self, request, *args, **kwargs):
        # surveys = Lineitem.objects.filter(active=2,activity__active=2,project__active=2).exclude(activity__capture_level_type=2).distinct('activity_id').select_related('activity','project').order_by("activity_id","activity__survey_order")
        project_theme = dict(ProjectTheme.objects.filter(active=2).values_list('project_id','project_theme__name'))
        beneficiaries = dict(BeneficiaryType.objects.filter(active=2).values_list('id','name'))
        survey_beneficiaries,location_level = {},{}
        boundary_level_dict = {str(obj.id):obj for obj in BoundaryLevel}
        
        for i in surveys:
            if i.activity.survey_type == 0:
                survey_beneficiaries[i.activity_id] = beneficiaries.get(i.activity.object_id)
            elif i.activity.survey_type == 1:
                for j in i.activity.config:
                    for key in j.keys():
                        indexvalue = key.split('_')[-1]
                        if j[key] == "BeneficiaryType":
                            survey_beneficiaries[i.activity_id] = beneficiaries.get(int(j.get('object_id_' + indexvalue)))

                        if j[key] == "BoundaryLevel":
                            level = boundary_level_dict.get(j.get('object_id_'+indexvalue))
                            if not level:
                                for obj_id, obj in boundary_level_dict.items():
                                    if str(obj.code) == j.get('object_id_'+indexvalue):
                                        level = obj
                                        break
                            location_level[i.activity_id] = level

        search_txt = request.GET.get('s')
        if search_txt:
            surveys = surveys.filter(activity__name__icontains = search_txt)
        object_list = get_pagination(request, surveys)
        return render(request,self.template_name,locals())


@method_decorator(login_required, name='dispatch')
class ImportResponses(View):
    template_name = 'survey_forms/upload_profile.html'
    max_file_size = settings.RESPONSE_IMPORT['MAX_FILE_SIZE']
    max_file_size_in_mb = max_file_size / 1024 / 1024
    def get(self, request, pk):
        heading = "Student Data Upload"
        project = Project.objects.select_related('partner_mission_mapping__mission','partner_mission_mapping__partner','district').get(id=pk)
        profile_fields = {'Name':project.name,'Mission':project.partner_mission_mapping.mission.name,'Partner':project.partner_mission_mapping.partner.name,'District':project.district.name,'Start Date':project.start_date or '-','End Date':project.end_date or '-'}

        # validating the project have any school 
        school_exists = BeneficiaryResponse.objects.filter(active=2,survey_id=1,address_2=Boundary.objects.get(active=2,boundary_level_type_id=2,code = project.district_id).id)

        uploaded_responses_list = ResponseImportFiles.objects.filter(active=2,project_id=pk).select_related('survey','project').order_by('-created')
        object_list = get_pagination(request, uploaded_responses_list)
        return render(request,self.template_name,locals())

    def post(self, request, pk):
        file = request.FILES.get('file')
        survey_id = request.POST.get('ben_type')
        timestamp_str = datetime.now().strftime("%Y%b%d%H%M%S")
        file_name_without_extension = file.name.split('.')[0] 
        # TODO: need to create a excel file for format create
        format_file = f"/response_file_format/survey_{survey_id}_format.xlsx"
        # import ipdb;ipdb.set_trace()
        # Check file size
        if file.size > self.max_file_size:
            messages.error(request, "File has been rejected. Please check file size and try again.")
            return render(request, self.template_name, locals())
        
        # Validate Excel file format and headers
        if not (self.validate_excel_file(file) and self.check_header_equality(request,file, settings.MEDIA_ROOT + format_file,survey_id,pk)):
            messages.error(request, "File has been rejected. Please download file format and try again.")
            return render(request, self.template_name, locals())
        
        # Read Excel file
        df = pd.read_excel(file,dtype=str)
        if df.empty:
            messages.error(request, "Please ensure that the file contains data and try again.")
            return render(request, self.template_name, locals())

        # Perform custom validation
        df = questions_validation(df, survey_id, pk)
        if 'Error Message' in df.columns and df['Error Message'].notnull().any():
            # Prepare error Excel file
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
            response = HttpResponse(excel_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename={file_name_without_extension}_{timestamp_str}.xlsx'
            return response
            
        # Save response details
        resp_obj,_ = ResponseImportFiles.objects.update_or_create(survey_id = survey_id,project_id = pk,
            status__in=['Uploaded'],
            defaults={
                "user_id":request.user.id,
                "response_image": file,
                "status": "Uploaded",
                "modified": datetime.now(),
                "error_details": "",
            })
        logger.info(f'ResponseImportFiles {str(resp_obj.id)} created')
        self.call_zip_process(survey_id,pk)
        messages.success(request, "File has been uploaded successfully.")
        return render(request,self.template_name,locals())

    def validate_excel_file(self,file):
        try:
            pd.read_excel(file)
            return True
        except Exception as e:
            return False

    def check_header_equality(self,request, file1, file2, survey_id, project_id):
        df1 = pd.read_excel(file1)
        if not os.path.exists(file2):
            data_response = generate_excel(request,survey_id, project_id)
        if 'Error Message' in df1.columns:
            df1.drop(columns='Error Message', inplace=True)
        excel_file = BytesIO(data_response.content)
        df2 = pd.read_excel(excel_file)
        result = set(df2.columns).issubset(set(df1.columns))
        return result

    def call_zip_process(self,s_value,p_value):
        # Command to activate the environment and then run the Django command
        command = f'{settings.PROJECT_ENV}/bin/python3 {settings.BASE_DIR}/manage.py import_responses -s {s_value} -p {p_value}'
        # Run the command using bash
        # subprocess.Popen(command, cwd=project_path, shell=True, executable='/bin/bash')

        # t1 = datetime.now()
        # This command runs: python manage.py import_responses -s <survey_id> -p <project_id>
        # subprocess.Popen(['python3', 'manage.py', 'import_responses', '-s', str(s_value), '-p', str(p_value)])
        subprocess.Popen(command, cwd=settings.BASE_DIR, shell=True, executable='/bin/bash')
        # t2 = datetime.now()
        # time_delta = (t2-t1)
        # logger.info(f'Importing {str(s_value)} , {str(p_value)} - started :{str(t1)} , ended :{str(t2)} - time taken:' + str(time_delta))
        # logger.info(command)


from django.template.defaultfilters import slugify

def generate_excel(request,survey_id,project_id):
    # Define your headers
    unique_ids = settings.RESPONSE_IMPORT['unique_id']
    headers = ['Generation Key','Project']
    survey_questions = load_data_to_cache_questions()
    cache_surveys = load_data_to_cache_survey()
    survey = cache_surveys.get(str(survey_id))
    project = Project.objects.get(id=project_id)
    
    questions = list(Question.objects.filter(block__survey_id=survey_id).exclude(active=0).order_by('code').values('id','qtype','text','api_json','parent_id','is_grid'))
    if survey.get('data_entry_level_id') == 1 or (not bool(survey.get('survey_type')) and  any(item['qtype'] == 'AW' for item in questions)): #Location based activity or Beneficiary survey
        boundary_levels = load_data_to_cache_boundary_level()
        # boundary_levels = list(BoundaryLevel.objects.filter(active=2).order_by('code').values_list('name',flat=True))
        headers.extend([i[2] for i in boundary_levels])
    
    headers.extend([i['text'] for i in questions if (i["qtype"] not in ["GD","AI","AW"]) and (not i['parent_id'] )])    
    # for i in questions:
    #     if (i["qtype"] not in ["GD","AI"]) and (not i['parent_id'] ):
    #         headers.append(i['text'])
    api_question = list(filter(lambda x: x['qtype'] in ['AI'],questions))
    if api_question and api_question[0].get('api_json',{}).get('lname_que_id'):
        lname_que_id = api_question[0].get('api_json',{}).get('lname_que_id').split(',')
        parent_question = survey_questions.get(lname_que_id[0])
        parent_survey_id = parent_question.get('survey_id')
        parent_survey = cache_surveys.get(str(parent_survey_id))
        unique_id = unique_ids.get(str(parent_survey_id))

        parent_survey_name = parent_survey.get('name')
        headers.append(parent_survey_name + '--' + survey_questions.get(unique_id,{}).get('text'))
    
    gd_question = list(filter(lambda x: x['qtype'] in ['GD'],questions))
    for qu in gd_question:
        gd_child_question = list(filter(lambda x: x['parent_id'] == qu['id'],questions))
        headers.extend([f"{qu['text']}--{i['text']}.{j['text']}" for i in gd_child_question if i['is_grid'] for j in gd_child_question if not j['is_grid']])


    # Create a DataFrame with the headers
    df = pd.DataFrame(columns=headers)
    df.at[0, 'Project'] = project.name
    if survey_id == '1':
        df.at[0, 'District'] = project.district.name.strip()
        df.at[0, 'State'] = project.district.state.name.strip()

    # Specify the path to save the file
    # folder_path = os.path.join(settings.MEDIA_DIR, 'response_file_format')
    # file_path = os.path.join(folder_path, f'survey_{survey_id}_format.xlsx')

    # # Ensure the directory exists
    # os.makedirs(folder_path, exist_ok=True)

    # # Save the file to the specified directory
    # with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
    #     df.to_excel(writer, index=False, sheet_name='Sheet1')

    # Create a response object and specify content type
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    file_name = slugify(f"{project.name[:10]}_{survey.get('id')}")
    response['Content-Disposition'] = f'attachment; filename="{file_name}_format.xlsx"'

    # Use pandas to write the DataFrame to the response
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')

    return response
    
class GetSurvey(APIView):
    def get(self, request, sid):
        try:
            survey = Survey.objects.get(id=sid)
            survey_details = {}
            survey_details['name'] = survey.name
            survey_details['survey_type'] = survey.survey_type
            survey_details['periodicity'] = survey.periodicity
            survey_details['display_type'] = survey.display_type
            survey_details['theme_id'] = survey.theme.id if survey.theme else ""
            survey_details['beneficiary_type_id'] = ""
            survey_details['location_id'] = ""
            survey_details['type'] = 3
            survey_details['cp_level'] = survey.capture_level_type
            if survey.survey_type == 0:
                survey_details['type'] = 2
                survey_details['beneficiary_type_id'] = survey.object_id
            elif survey.survey_type == 1:
                get_updated_survey_details(survey_details, survey)
            return Response({'status': 2, 'survey_details': survey_details})
        except Exception as e:
            return Response({'status': 0, 'message': 'Survey doesnt exist', 'error': e.args[0]})


def get_updated_survey_details(survey_details, survey):
    """
    Inline function for updating the survey details dictionary
    if it is extended survey.
    Return the updated dictionary with beneficiary type and location level
    """
    values_list = []
    for config in survey.config:
        for k in config.keys():
            values_list.extend(config.values())
            ids = k.split('_')[-1]
            if str(config[k]) == 'BoundaryLevel':
                survey_details['location_id'] = int(
                    config.get('object_id_' + ids))
            if str(config[k]) == 'BeneficiaryType':
                survey_details['beneficiary_type_id'] = int(
                    config.get('object_id_' + ids))
           # for role type activity
            if str(config[k]) == 'RoleTypes':
                survey_details['role_id'] = int(
                    config.get('object_id_' + ids))
    if 'BoundaryLevel' in values_list:
        survey_details['type'] = 1
    if 'BeneficiaryType' in values_list:
        survey_details['type'] = 2
    if 'RoleTypes' in values_list:
        survey_details['type'] = 4
    return None

@method_decorator(login_required, name='dispatch')
class SurveyDeactivate(View):
    def get(self,request,activityid):
        try:
            activity = Survey.objects.get(id=activityid)
            if activity.active:
                if request.user.is_authenticated:
                    activity.active = 3 # Making the Activty as Inactive
                    activity.deactivated_reason = request.GET.get("reason")
                    activity.deactivated_user = request.user 
                    # activity.deactivated_date  = datetime.datetime.now() 
                    activity.deactivated_date  = timezone.localtime(timezone.now())
                    activity.save()
                    record_deactivate(request,'survey',activityid,request.GET.get("reason"),activity.active)
        except:
            pass 
        return HttpResponseRedirect('/survey/edit/{0}/'.format(activityid))
            
@method_decorator(login_required, name='dispatch')
class QuestionDeactivate(View):
    def get(self,request,questionid):
        try:
            question = Question.objects.get(id=questionid)
            if question.active:
                if request.user.is_authenticated:
                    question.active = 3 # Making the Activty as Inactive
                    question.deactivated_reason = request.GET.get("reason")
                    question.deactivated_user = request.user 
                    question.deactivated_date  = timezone.localtime(timezone.now())
                    question.save()
                    record_deactivate(request,'question',questionid,request.GET.get("reason"),question.active)
        except:
            pass 
        return HttpResponseRedirect('/question/edit/{0}/'.format(questionid))

@method_decorator(login_required, name='dispatch')
class ChoiceDeactivate(View):
    def get(self,request,choiceid):
        try:
            choice = Choice.objects.get(id=choiceid)
            if choice.active:
                if request.user.is_authenticated:
                    choice.active = 3 # Making the Activty as Inactive
                    choice.deactivated_reason = request.GET.get("reason")
                    choice.deactivated_user = request.user 
                    choice.deactivated_date  = timezone.localtime(timezone.now())
                    choice.save()
                    record_deactivate(request,'choice',choiceid,request.GET.get("reason"),choice.active)
        except:
            pass 
        return HttpResponseRedirect('/choice/edit/{0}/'.format(choiceid))
