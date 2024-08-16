# query_view.py

from django.http import HttpResponse
from django.template import loader
from django.urls import path
from django.db import connection

# View to handle multiple queries and render the response
def query_view(request):
    # List of SQL queries
    queries = [
        """select a.id as form_id, a.name as form_name, b.json_count as "jsonanswer_count (A)", c.response_count as "beneficiaryresponse_count (B)", (b.json_count - c.response_count) as "missing_data (A-B)" from (select id, name from survey_survey where active !=0 and survey_type = 0 ) as a left outer join (select survey_id, count(*) as json_count from survey_jsonanswer where active != 0 and survey_id in (select id from survey_survey where active != 0 and survey_type = 0) group by survey_id ) as b on a.id = b.survey_id left outer join (select survey_id, count(*) as response_count from survey_beneficiaryresponse where active != 0 and survey_id in (select id from survey_survey where active != 0 and survey_type = 0) group by survey_id ) as c on a.id = c.survey_id""",
        """select a.id as form_id, a.name as form_name, b.missing_ben_count as missing_beneficiaries, b.max_created::date as activity_created_max_date, b.min_created::date as activity_created_min_date from (select id, name from survey_survey where active !=0 and survey_type = 1 ) as a left outer join (select x1.survey_id, count(*) as missing_ben_count, max(x1.created) as max_created, min(x1.created) as min_created from survey_jsonanswer x1 left outer join survey_beneficiaryresponse x2 on x1.cluster->>'BeneficiaryResponse' = x2.creation_key where x1.active != 0 and x1.survey_id in (select id from survey_survey where active != 0 and survey_type = 1) and x2.id is null group by x1.survey_id ) as b on a.id = b.survey_id where b.missing_ben_count > 0"""
    ]
    
    results = []
    
    # Execute each query
    for query in queries:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            headers = [col[0] for col in cursor.description]
            results.append({
                'headers': headers,
                'rows': rows
            })
    
    # Render the results in a template
    template = loader.get_template('custom_query.html')
    context = {
        'results': results,
    }
    return HttpResponse(template.render(context, request))

# URL pattern to map the view
urlpatterns = [
    path('sb-query/', query_view, name='query_view'),
]

# Add this URL pattern to your project's urlpatterns in urls.py
