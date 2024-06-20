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
import bleach

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
        surveys = Survey.objects.filter().exclude(active=0).order_by("survey_order")
        search_txt = request.GET.get('s')
        if search_txt:
            surveys = surveys.filter(name__icontains = search_txt)
        object_list = get_pagination(request, surveys)
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
        # beneficiary_types = BeneficiaryType.objects.filter(active=2).exclude(parent=None).order_by('btype_order')
        levels = BoundaryLevel.objects.all()
        # roles = RoleTypes.objects.filter(active=2)
        return render(request,self.template_name,locals())
    

class SurveyEdit(View):
    template_name = 'survey_forms/survey_add.html'
    def get(self, request, pk, *args, **kwargs):
        edit = True
        survey_type_choices = SURVEY_TYPE_CHOICES
        periodicity_choices = PERIODICITY_CHOICES
        survey_deactivate_reasons =  SURVEY_DEACTIVATE_REASON
        themes = MasterLookUp.objects.filter(parent__slug="theme")
        capture_level_choices= CAPTURE_LEVEL_CHOICES
        # beneficiary_types = BeneficiaryType.objects.filter(active=2).exclude(parent=None).order_by('btype_order')
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
                return HttpResponseRedirect('/manage/question/add/' + str(pk) + '/' + str(question.id) + '/')
            return HttpResponseRedirect('/manage/questions/' + str(pk) + '/')
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
        response = {'status': "success", "message": "successfully done"}
        serializer = LinkageListingSerializer(data=request.data)
        if serializer.is_valid():
            data_dict = {'content_type':ContentType.objects.get_for_model(BeneficiaryResponse),
                'content_type1':ContentType.objects.get_for_model(BeneficiaryResponse),
                'relation':None,
                'survey_relation':1
                }
            linkage_list,flag = get_common_linkage_details(request,data_dict)
            response.update({'linkages': linkage_list})
        else:
            return get_serializer_errors(serializer)
        return Response(response)    

