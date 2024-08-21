from django.template.defaulttags import register
from survey.models import Question, Choice
from datetime import datetime, timedelta
from mfv_mis.settings import *
from cache_configuration.views import *
from django.db import connection
import json
from survey.form_views import load_data_to_cache_choices
from survey.form_views import get_result_query, get_financial_year_dates




@register.simple_tag
def get_validation_code(q_id):
    from survey.form_views import load_data_to_cache_question_validation
    questions = load_data_to_cache_question_validation()
    # questions = [questions.get(str(self.id),{})]
    # questions = QuestionValidation.objects.filter(question=self)
    min_max_dict = {'min_length': '', 'max_length': '', 'min': '',
                        'max': ''}
    validation_dict = {}
    # "charactersType": [i.get('id') for i in questions if questions]
    # for i in questions:
    i = questions.get(str(q_id))
    if i and (i.get('code') == 'A' or i.get('code') == 'AN'):
        min_max_dict.update({'min_length': i.get('min_value'), 'max_length':
            i.get('max_value')})
    elif i and i.get('code') == 'N':
        min_max_dict.update({'min': i.get('min_value'), 'max':
            i.get('max_value')})
    elif i and i.get('code') == 'DT' and i.get('min_value') and i.get('max_value'):
        min=i.get('min_value')[4:]+'-'+i.get('min_value')[2:4]+'-'+i.get('min_value')[:2] if i.get('min_value') != '00000000' else datetime.today().strftime("%Y-%m-%d")
        max=i.get('max_value')[4:]+'-'+i.get('max_value')[2:4]+'-'+i.get('max_value')[:2] if i.get('max_value') != '00000000' else datetime.today().strftime("%Y-%m-%d")
        min_max_dict.update({'min': min, 'max':max})

    validation_dict.update({'MinMax': min_max_dict})
    msg,code = '',''
    if i :
        msg=i.get('message','')
        code=i.get('code','')
    validation_dict.update({'message': msg,'code':code})

    return validation_dict

@register.filter
def auto_fill_date(request, survey_id):
    start_date, end_date = get_financial_year_dates()
    ben=request.GET.get('ben','')
    vlu_list = ''
    if ben and survey_id == 5:
        query='select js.id,survey_id,js.response,s.slug,creation_key,js.created,js.modified,js.active,s.extra_config from survey_jsonanswer js inner join survey_survey s on s.id = js.survey_id where js.active != 0 and s.id=4 and js.cluster->>\'BeneficiaryResponse\' = \'{0}\''.format(ben)
        query=query.replace("@@financial_year","and (js.created at time zone 'Asia/Kolkata')::date >='{0}' and (js.created at time zone 'Asia/Kolkata')::date <= '{1}'".format(start_date, end_date))
        result = get_result_query(query)
        vlu_list = []
        for val in result:
            # import ipdb; ipdb.set_trace()
            auto_vlu = json.loads(val[2]).get('285')
            name = Choice.objects.get(question_id=285,id=auto_vlu).text
            vlu_list.append(name)

    if vlu_list:
        return vlu_list[-1]
    else:
        return vlu_list

@register.filter
def last_record_edit(request, survey_id):
    start_date, end_date = get_financial_year_dates()
    ben=request.GET.get('ben','')
    dates = ''
    if ben and survey_id in [7,9]:
        query='select js.id,survey_id,js.response,s.slug,creation_key,js.created,js.modified,js.active,s.extra_config from survey_jsonanswer js inner join survey_survey s on s.id = js.survey_id where js.active != 0 and s.id=\'{1}\' and js.cluster->>\'BeneficiaryResponse\' = \'{0}\''.format(ben,survey_id)
        query=query.replace("@@financial_year","and (js.created at time zone 'Asia/Kolkata')::date >='{0}' and (js.created at time zone 'Asia/Kolkata')::date <= '{1}'".format(start_date, end_date))
        result = get_result_query(query)
        dates = []
        for val in result:
            dates.append(val[4])
    if dates:
        return dates[-1]
    else:
        return dates

@register.filter
def display_last_date(request, survey_id):
    start_date, end_date = get_financial_year_dates()
    ben=request.GET.get('ben','')
    latest_date = ''
    if ben and survey_id in [7,9]:
        query='select js.id,survey_id,js.response,s.slug,creation_key,js.created,js.modified,js.active,s.extra_config from survey_jsonanswer js inner join survey_survey s on s.id = js.survey_id where js.active != 0 and s.id=\'{1}\' and js.cluster->>\'BeneficiaryResponse\' = \'{0}\''.format(ben,survey_id)
        query=query.replace("@@financial_year","and (js.created at time zone 'Asia/Kolkata')::date >='{0}' and (js.created at time zone 'Asia/Kolkata')::date <= '{1}'".format(start_date, end_date))
        result = get_result_query(query)
        dates = []
        for val in result:
            data = json.loads(val[2]).get('509') if survey_id == 7 else json.loads(val[2]).get('512')
            values = [sub_dict['352'] if survey_id == 7 else sub_dict['518'] for sub_dict in data.values()]
            dates.extend(values)
        if len(dates) != 0:
            date_objects = [datetime.strptime(date, '%d-%m-%Y') for date in dates]
            latest_date_max_value = max(date_objects)
            new_date_obj = latest_date_max_value + timedelta(days=1)
            latest_date = new_date_obj.strftime('%Y-%m-%d')
    return latest_date

@register.simple_tag
def get_childs(q_id):
    # Caching the child questions based on parent question
    # filtering block based questions
    query = "SELECT jsonb_object_agg(parent_id, question_info) FROM ( SELECT a.parent_id, jsonb_agg( jsonb_build_object( 'id', a.id,'qtype',a.qtype, 'text', a.text, 'is_grid', a.is_grid, 'mandatory', a.mandatory,'api_json', a.api_json,'form_question_number',a.form_question_number,'is_editable', a.is_editable,'api_qtype',a.api_qtype,'parent',a.parent_id,'training_config',a.training_config) ORDER BY a.question_order ) question_info FROM survey_question a WHERE a.active = 2 and a.parent_id is not null GROUP BY parent_id ) AS x"

    cache_key_questions = INSTANCE_CACHE_PREFIX+'get_childs'
    child_questions =  cache.get(cache_key_questions)
    if not child_questions:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            child_questions = json.loads(result[0][0])
        # child_questions=Question.objects.filter(parent=self,active=2).order_by('question_order').value
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_questions,child_questions,CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return child_questions.get(str(q_id))


@register.simple_tag
def is_skip_question(q_id):
    choice_cache_dict = load_data_to_cache_choices()
    next_question_choices = choice_cache_dict.get(str(q_id),[])
    for k in next_question_choices:
        if k.get('skip_question_ids'):
            return True
    return False

@register.simple_tag
def get_inner_questions(q_id):
    question_ids = []
    choice_cache_dict =  load_data_to_cache_choices()
    choice  = choice_cache_dict.get(str(q_id),[])
    for i in choice:
        for j in i.get('skip_question_ids'):
            question_ids.append(j)
            has_skip_questions = False
            next_question_choices = choice_cache_dict.get(str(j),[])
            for k in next_question_choices:
                if k.get('skip_question_ids'):
                    has_skip_questions = True
            if has_skip_questions:
                # next_question = Question.objects.get(id = j)
                question_ids.extend(get_inner_questions(j))
    return list(set(question_ids))

@register.simple_tag
def choice_list(q_id):
    choice_cache_dict = load_data_to_cache_choices()
    return choice_cache_dict.get(str(q_id))

@register.simple_tag
def disabled_list(q_id):
    disabled_value = 0
    if q_id:
        disabled_index = Choice.objects.filter(question_id=q_id,is_other_choice=True)
        if disabled_index.exists():
            disabled_value = disabled_index.first().id
    return disabled_value

@register.simple_tag
def get_questions(block_id):
    # Caching the questions based on block
    # filtering block based questions
    query = "SELECT jsonb_object_agg(block_id, question_info) FROM ( SELECT a.block_id, jsonb_agg( jsonb_build_object( 'id', a.id,'qtype',a.qtype, 'text', a.text, 'is_grid', a.is_grid, 'mandatory', a.mandatory,'api_json', a.api_json,'form_question_number',a.form_question_number,'is_editable', a.is_editable,'api_qtype',a.api_qtype,'parent',a.parent_id,'training_config',a.training_config) ORDER BY a.question_order ) as question_info FROM survey_question a WHERE a.active = 2 and a.parent_id is null GROUP BY block_id ) AS x"

    cache_key_questions = INSTANCE_CACHE_PREFIX+'get_questions'
    block_questions =  cache.get(cache_key_questions)
    if not block_questions:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            block_questions = json.loads(result[0][0])
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_questions,block_questions,CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return block_questions.get(str(block_id))

@register.simple_tag
def get_row_questions(q_id):
    parents = get_childs(q_id)
    filtered_data = [item for item in parents if item.get('is_grid')]
    return filtered_data

@register.simple_tag
def get_column_questions(q_id):
    parents = get_childs(q_id)
    filtered_data = [item for item in parents if not item.get('is_grid')]
    return filtered_data