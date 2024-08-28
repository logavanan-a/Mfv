from django.template.defaulttags import register
from cache_configuration.views import *
# from configuration_settings.django_config_views import date_validate
import re
from datetime import datetime,date
from survey.models import JsonAnswer
# imported register
import json
from survey.form_views import get_result_query
from django.forms.models import model_to_dict
from mfv_mis.settings import DATE_DISPLAY_FORMAT,MONTH_DISPLAY_FORMAT,INSTANCE_CACHE_PREFIX


# Register function as template tag
@register.filter
def get_item(dictionary, key):
    try:
        # Gets item from dictionary
        return dictionary.get(key)
    except:
        # Returns None if key is not found
        return ''

@register.filter
def get_item_ans(json_answer,header):
    json_answer = model_to_dict(json_answer)

    try:

        if json_answer.get('survey') == 7:
            response_data = json_answer.get('response')
            if '509' in response_data:
                follow_data = response_data.get('509')
                key = list(follow_data.keys())[-1]
                date_with_format = follow_data.get(key)
            
                if header.get('qtype') == 'S':
                    cache_key_choices = INSTANCE_CACHE_PREFIX+'survey_listing_page_answer_choices'#_for_'+str(json_answer.get('survey_id'))
                    survey_heading_choices =  cache.get(cache_key_choices)
                    # print(cache_key_question)
                    # choices=survey_heading_choices.get(header.get('id'))
                    choice_answer=json_answer.get('response').get(str(header.get('id')))
                    selected_choice=next(item for item in survey_heading_choices if str(item.get('id') or '') == choice_answer)
                    return selected_choice.get('text')
                elif header.get('qtype') == 'D':
                    date_format = re.compile(r'\d{2}-\d{2}-\d{4}')
                    date_with_format=date_with_format.get(str(header.get('id')))
                    age=None
                    if not date_format.match(date_with_format) and not header.get('training_config').get('month'):
                        date_object = datetime.strptime(date_with_format, '%Y-%m-%d')
                        date_with_format=date_object.strftime(DATE_DISPLAY_FORMAT)
                    elif not header.get('training_config').get('month'):
                        date_object = datetime.strptime(date_with_format, '%d-%m-%Y')
                        date_with_format=date_object.strftime(DATE_DISPLAY_FORMAT)
                    elif header.get('training_config').get('month'):
                        date_object = datetime.strptime(date_with_format, '%m-%Y')
                        date_with_format=date_object.strftime(MONTH_DISPLAY_FORMAT)
                        
                    if header.get('training_config').get('dob'):
                        today = date.today()
                        age=today.year - date_object.year - ((today.month, today.day) < (date_object.month, date_object.day))
                        date_with_format=date_with_format+"("+str(age)+")"
                    return date_with_format
            
            datas = date_with_format.get(str(header.get('id')))
            if not datas:
                datas = '-'

        else:
            if json_answer.get('response').get(str(header.get('id')),'None') == 'None' and header.get('qtype') != 'AW': 
                return '-'
            elif header.get('qtype') == 'S':
                cache_key_choices = INSTANCE_CACHE_PREFIX+'survey_listing_page_answer_choices'#_for_'+str(json_answer.get('survey_id'))
                survey_heading_choices =  cache.get(cache_key_choices)
                # print(cache_key_question)
                # choices=survey_heading_choices.get(header.get('id'))
                choice_answer=json_answer.get('response').get(str(header.get('id')))
                selected_choice=next(item for item in survey_heading_choices if str(item.get('id') or '') == choice_answer)
                return selected_choice.get('text')
            elif header.get('qtype') == 'R':
                cache_key_choices = INSTANCE_CACHE_PREFIX+'survey_listing_page_answer_choices'#_for_'+str(json_answer.get('survey_id'))
                survey_heading_choices =  cache.get(cache_key_choices)
                # print(cache_key_question)
                # choices=survey_heading_choices.get(header.get('id'))
                choice_answer=json_answer.get('response').get(str(header.get('id')))
                selected_choice=next(item for item in survey_heading_choices if str(item.get('id') or '') == choice_answer)
                return selected_choice.get('text')
            elif header.get('qtype') == 'SM':
                # import ipdb;ipdb.set_trace()
                cache_key_lookups = INSTANCE_CACHE_PREFIX+'all_master_lookup_caching'
                survey_heading_lookups =  cache.get(cache_key_lookups)
                lookup_answer=json_answer.get('response').get(str(header.get('id')))
                pattern = r'^\[\d+(,\d+)*\]$'
                if re.match(pattern, lookup_answer):
                    lookup_answer=json.loads(lookup_answer)
                else:
                    lookup_answer=[int(lookup_answer)]
                selected_lookup=next(item for item in survey_heading_lookups if item.get('id') in lookup_answer)
                return selected_lookup.get('name')
            elif header.get('qtype') == 'AI':
                answer=json_answer.get('response').get(str(header.get('id')))
                json_name = JsonAnswer.objects.get(creation_key=answer).response.get('235')
                return json_name
            elif header.get('qtype') == 'AW':
                cache_key_bondaries = INSTANCE_CACHE_PREFIX+'all_boundary_caching'
                survey_heading_boundaries =  cache.get(cache_key_bondaries)
                address=json_answer.get('response').get('address')
                final_address=get_last_level(address)
                state=final_address.get('1')
                district=final_address.get('2')
                final_state=[item for item in survey_heading_boundaries if str(item.get('id') or '') == state]
                final_district=[item for item in survey_heading_boundaries if str(item.get('id') or '') == district]
                str_res = '{0}'.format(final_state[0].get('name'))
                if final_district:
                    str_res='{0}<br/>({1})'.format(final_district[0].get('name'),final_state[0].get('name'))
                return str_res
            elif header.get('qtype') == 'C':
                answer = ast.literal_eval(json_answer.get('response').get(str(header.get('id'))))
                cache_key_choices = INSTANCE_CACHE_PREFIX+'survey_listing_page_answer_choices'#'survey_listing_page_answer_choices_for_'+str(survey_id)
                survey_heading_choices =  cache.get(cache_key_choices)
                res=[]
                selected_choice=[res.append(item.get('text')) for item in survey_heading_choices if item.get('id') in  answer]
                return ', '.join(res)
            elif header.get('qtype') == 'D':
                date_format = re.compile(r'\d{2}-\d{2}-\d{4}')
                date_with_format=json_answer.get('response').get(str(header.get('id')))
                age=None
                if not date_format.match(date_with_format) and not header.get('training_config').get('month'):
                    date_object = datetime.strptime(date_with_format, '%Y-%m-%d')
                    date_with_format=date_object.strftime(DATE_DISPLAY_FORMAT)
                elif not header.get('training_config').get('month'):
                    date_object = datetime.strptime(date_with_format, '%d-%m-%Y')
                    date_with_format=date_object.strftime(DATE_DISPLAY_FORMAT)
                elif header.get('training_config').get('month'):
                    date_object = datetime.strptime(date_with_format, '%m-%Y')
                    date_with_format=date_object.strftime(MONTH_DISPLAY_FORMAT)
                    
                if header.get('training_config').get('dob'):
                    today = date.today()
                    age=today.year - date_object.year - ((today.month, today.day) < (date_object.month, date_object.day))
                    date_with_format=date_with_format+"("+str(age)+")"
                return date_with_format
            datas = json_answer.get('response').get(str(header.get('id')))
    except:
        return '-'
    return datas

#get last level of dictionary in nested dictinary

def get_last_level(d):
    for key, value in d.items():
        if not isinstance(value, dict):
            return d
        return get_last_level(value)

@register.filter
def get_question_text(q_id,survey_id):
    try:
        cache_key_choices = INSTANCE_CACHE_PREFIX+'survey_heading_questions_for_'+str(survey_id)
        survey_questions =  cache.get(cache_key_choices)
        question_text=survey_questions.get(id=q_id)
        return question_text.get('text')
    except:
        return '-'

import ast
from django.utils.safestring import mark_safe
@register.simple_tag
def get_answer_text(survey_id,answer,question):
    cache_key_choices = INSTANCE_CACHE_PREFIX+'survey_listing_page_answer_choices'#'survey_listing_page_answer_choices_for_'+str(survey_id)
    cache_key_question= INSTANCE_CACHE_PREFIX+'survey_heading_questions_for_'+str(survey_id)
    survey_heading_choices =  cache.get(cache_key_choices)
    survey_heading_questions =  cache.get(cache_key_question)
    # question=next(item for item in survey_heading_questions if item.get('id') == q_id)
    # print(question,'---------',type(answer))
    try:
        if (answer == 'None' or answer == None) and question.get('qtype') != 'AW': 
            return '-'
        elif question.get('qtype') == 'S':
            # cache_key_choices = 'survey_listing_page_answer_choices'
            # survey_heading_choices =  cache.get(cache_key_choices)
            answer = ast.literal_eval(answer) if type(ast.literal_eval(answer)) == list else [ast.literal_eval(answer)]
            selected_choice=[item.get('text') for item in survey_heading_choices if item.get('id','') in answer]
            return ', '.join(selected_choice)
        elif question.get('qtype') == 'SM':
            cache_key_lookups = INSTANCE_CACHE_PREFIX+'all_master_lookup_caching'
            survey_heading_lookups =  cache.get(cache_key_lookups)
            selected_lookup=next(item for item in survey_heading_lookups if str(item.get('id') or '') == answer)
            return selected_lookup.get('name')
        elif question.get('qtype') == 'AW':
            cache_key_bondaries = INSTANCE_CACHE_PREFIX+'all_boundary_caching'
            survey_heading_boundaries =  cache.get(cache_key_bondaries)
            final_address=get_last_level(answer)
            state=final_address.get('1')
            district=final_address.get('2')
            result=[item for item in survey_heading_boundaries if str(item.get('id') or '') in [state,district]]
            str_res = '{0}'.format(result[0].get('name'))
            if len(result) > 1:
                str_res='{1}({0})'.format(result[1].get('name'),result[0].get('name'))
            return str_res
        elif question.get('qtype') == 'AI':
            json_name = JsonAnswer.objects.get(creation_key=answer).response.get('231')
            return json_name
        elif question.get('qtype') == 'C':
            # cache_key_choices = 'survey_listing_page_answer_choices'
            # survey_heading_choices =  cache.get(cache_key_choices)
            res=[]
            selected_choice=[res.append(item.get('text')) for item in survey_heading_choices if item.get('id') in  json.loads(answer)]
            return ', '.join(res)

        elif question.get('qtype') == 'D':
            date_format = re.compile(r'\d{2}-\d{2}-\d{4}')
            age=None
            if not date_format.match(answer) and not question.get('training_config').get('month'):
                date_object = datetime.strptime(answer, '%Y-%m-%d')
                answer=date_object.strftime(DATE_DISPLAY_FORMAT)
            elif not question.get('training_config').get('month'):
                date_object = datetime.strptime(answer, '%d-%m-%Y')
                answer=date_object.strftime(DATE_DISPLAY_FORMAT)
            elif question.get('training_config').get('month'):
                date_object = datetime.strptime(answer, '%m-%Y')
                answer=date_object.strftime(MONTH_DISPLAY_FORMAT)
            if question.get('training_config').get('dob'):
                today = date.today()
                age=today.year - date_object.year - ((today.month, today.day) < (date_object.month, date_object.day))
                answer=answer+"("+str(age)+")"
            return answer
        elif question.get('qtype') == 'GD':
            # choices=survey_heading_choices.get(question.get('id'))
            # child_questions =  get_childs()
            from survey.templatetags.form_builder_tags import get_childs
            child_questions = get_childs(question.get('id'))
            result = {}
            for i in child_questions:
                ans=answer.get(str(i.get('id')))    
                if ans: 
                    result.update({i.get('id'):get_answer_text(survey_id,ans,i)})
                # for k2,j in i.items():
                #     print(child_questions.get(k2),'iiii')
            # ans_text=next(item for item in survey_heading_choices if str(item.get('id')) == answer)
            return result
            # for item in survey_heading_choices:
            #     # print(item.get('id') == answer)
            #     if str(item.get('id')) == answer:

                    # print(answer,'-------------')
        # elif question.get('qtype') == 'H':
        #     selected_choice=next(item.get('text') for item in survey_heading_choices if str(item.get('id')) == answer)
        #     return selected_choice
            
    except:
        return '-'
    return answer


@register.filter
def get_item_str(dictionary, key):
    try:
        # Gets item from dictionary
        return dictionary.get(str(key))
    except:
        return '-'

@register.filter
def is_dict(value):
    #Checking the veriable is dict
    return isinstance(value, dict)

@register.filter
def get_dict_header(dictionary):
    try:
        first_key = next(iter(dictionary))
        first_value = dictionary.get(first_key)
        # Gets item from dictionary
        return first_value
    except:
        return '-'
    
@register.filter
def get_auto_fill(request,creation_key=None):
    ben=request.GET.get('ben','') if not creation_key else creation_key 
    val=''
    transformed_dict = {}
    query='select js.id,survey_id,js.response,s.slug,creation_key,js.created,js.modified,js.active,s.extra_config from survey_jsonanswer js inner join survey_survey s on s.id = js.survey_id where js.active != 0 and s.id =11 and js.cluster->>\'BeneficiaryResponse\' = \'{0}\' order by js.response->>\'445\''.format(ben)
    result = get_result_query(query)
    if ben:
        formatted_date = ''
        if len(result) != 0:
            date = json.loads(result[-1][2]).get('445')
            date_obj = datetime.strptime(date, '%d-%m-%Y')
            formatted_date = date_obj.strftime('%Y-%m-%d')
        secondary_query='select js.id,survey_id,js.response,s.slug,creation_key,js.created,js.modified,js.active,s.extra_config from survey_jsonanswer js inner join survey_survey s on s.id = js.survey_id where js.active != 0 and s.id=4 and js.cluster->>\'BeneficiaryResponse\' = \'{0}\' order by js.response->>\'405\''.format(ben)
        auto_fill_result = get_result_query(secondary_query)
        auto_fill_data = {}
        if len(auto_fill_result) != 0:
            auto_fill_data = json.loads(auto_fill_result[-1][2]).get('273')
        transformed_dict = {
            '445': formatted_date,
            '273': auto_fill_data
        }
    return transformed_dict


@register.filter
def index(lists,idx):
    try:
        return lists[idx]
    except:
        return '-'




    
