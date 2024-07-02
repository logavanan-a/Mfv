# from configuration_settings.templatetags.configuration_tags import user_level_boundary
from survey.models import Survey
from django.shortcuts import render
import psycopg2
import sys, traceback    
import logging
from django.db import connection
# from report_csv.models import *
from django.shortcuts import render,HttpResponse,HttpResponseRedirect
import datetime
# from reports.activity_reports import  load_user_details_to_session
import re
import pandas

logger = logging.getLogger(__name__)

def execute_query(conn,sql_query, typ):
    cursor = conn.cursor()
    #typ1 = insert
    #typ2 = update
    #typ3 = select
    #typ4 = stored procedure
    #typ5 = insert returning id
    #typ6 = DDL
    result = None
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(sql_query)
        if typ == 3 or typ == 4:
            result = cursor.fetchall()
        elif typ == 5:
            result = cursor.fetchone()[0]
    finally:
        if cursor:
            cursor.close()
    return result
    
# Create your views here.      
def download_file(request):
    from django.http import FileResponse
    from django.conf import settings
    from django.core.files.storage import FileSystemStorage
    survey_id = request.GET.get('survey_id')
    project_id = [str(i) for i in request.GET.getlist('project_id[]') if i != '' ]
    add_2 = [i for i in request.GET.getlist('district[]') if i != '' ]
    add_3 = [i for i in request.GET.getlist('block[]') if i != '']
    add_4 = [i for i in request.GET.getlist('grampanchayat[]') if i != '']
    add_5 = [i for i in request.GET.getlist('village[]') if i != '']
    filter_loc_values = {}
    filter_loc_values['address.2__id__'] = add_2
    filter_loc_values['address.3__id__'] = add_3
    filter_loc_values['address.4__id__'] = add_4
    filter_loc_values['address.5__id__'] = add_5
    date_filter = {}
    date_filter['from_date'] = request.GET.get('start_date')
    date_filter['to_date'] = request.GET.get('end_date')
    response = None
    delete_path = None
    delete_file_name = None
    if  survey_id and survey_id != '':
        try:
            #from settings
            survey = Survey.objects.get(id=survey_id)
            #TODO If Location filters are selected then query else return the comple dump file from survey report file_name
            # import ipdb;ipdb.set_trace()
            # filter_locations = load_user_details_to_session(request)
            if not project_id:
                file_name = survey.report_filename
                path = settings.MEDIA_ROOT +"/export_data/" 
            else:
                today = datetime.datetime.today()
                s_name = survey.name
                s_name = s_name.replace(" ","_")
                s_name = re.sub("[^A-Za-z0–9_]","",s_name)
                file_name = s_name + "-" + "{0}-{1}-{2}.xlsx".format(today.year,today.month,today.day)
                export_excel(request,survey_id, file_name,filter_loc_values ,date_filter,project_id)
                path = settings.MEDIA_ROOT +"/media/temp_export_data/"
                #delete only from temp folder - which stores the user related files generated at runtime
                delete_path = path
                delete_file_name = file_name
            response = HttpResponse(content_type='application/text charset=utf-8')
            file_exist = True
            fs = FileSystemStorage(path)
            if file_name is not None and file_name != '' and fs.exists(file_name):
                response = FileResponse(fs.open(file_name, 'rb'), content_type='application/force-download charset=utf-8')
                response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'
                file_exist = True
            else:
                file_exist = False
                response.write("File does not exist")
        finally:
            if delete_path and delete_file_name:
                delete_file(delete_path + delete_file_name)
    return response    

def delete_file(filename_with_path):
    import os
    if filename_with_path and filename_with_path not in ('.','..','...','./','*.*','*') and os.path.isfile(filename_with_path):
        os.remove(filename_with_path)
        
# def get_filter_values(request,loc_filter_column_map):
#     loc_filter_request_names = {1:'state_id',2:'region_id',3:'district_id',4:"cluster_id",5:"block_id",6:"gp_id",7:"village_id",8:"hamlet_id"}
#     filter_values_data = {}
#     filter_locations = load_user_details_to_session(request)
#     # req_data = request.GET
#     # if request.method == 'POST':
#     #     req_data = request.POST
#     # for loc_id, request_name in loc_filter_request_names.items():
#         # filter_value = req_data.get(request_name)
#     for index,item in enumerate(filter_locations):
#         filter_val = str(item[0]) if item[0] != 0 else None
#         filter_values_data.update({loc_filter_column_map.get(str(index+1)):filter_val})
#     return filter_values_data

# get the filter values for user location level - masterdata_boundary IDs mapped to the user
def get_filter_values(request,loc_filter_column_map):
    # import ipdb;ipdb.set_trace()
    filter_values_data = {}
    filter_locations = load_user_details_to_session(request)
    filter_values = []
    for loc_id in range(len(filter_locations)-1,-1,-1):
        if filter_locations[loc_id][0] != 0: 
            filter_values = [item[0] for item in filter_locations[loc_id][2]]
            break
    filter_values_data.update({loc_filter_column_map[str(loc_id+1)]:filter_values})
    return filter_values_data


# def build_query(table_name, columns_list, headers_list,filter_values):
#     columns_clause = ' '.join('{} as "{}",'.format(col_name, header_val) for col_name, header_val in zip(columns_list, headers_list))
#     where_clause = ""
#     for loc_column, loc_value in filter_values:
#         where_clause += '{} = {} and'.format(loc_column,loc_value)
#     sql_query = "select " + columns_clause[:-1] + " from " + table_name
#     if where_clause == "":
#         #remove the final " and" from the where_clause
#         sql_query = sql_query + " where " + where_clause[:-4]

# function to create query for the inline tables that include 
def build_query(request, table_name, columns_list, headers_list, filter_values, date_filter,main_table_name,survey_id,project_id):
    columns_clause = ' '.join('"{}" as "{}",'.format(col_name, header_val) for col_name, header_val in zip(columns_list, headers_list))
    where_clause = ""
    sql_query = ""
    # for loc_column, loc_value in filter_values.items():
    #     if loc_value != None:
    #         where_clause += '"{}" = {} and'.format(loc_column,loc_value)
    if project_id:
        where_clause = '"cluster.project_id"::integer in (' + ','.join(project_id) + ') and ' 
    from_date = date_filter['from_date']
    to_date = date_filter['to_date']
    if from_date != '' and  to_date != '':
        where_clause +=f"to_date(\"{columns_list[-1]}\",'YYYY-MM-DD') >= '{from_date}' and to_date(\"{columns_list[-1]}\",'YYYY-MM-DD') <= '{to_date}' and" 
    for loc_column, loc_value in filter_values.items():
        if loc_value != None and len(loc_value) > 0:
            loc_value = [str(item) for item in loc_value]
            where_clause += ' "{}" in ({}) and'.format(loc_column,','.join(loc_value))
    if where_clause != "":
        #remove the final " and" from the where_clause
        where_clause =  where_clause[:-4]
    #indicates the query is for the first sheet 
    if main_table_name == table_name:
        sql_query = "select " + columns_clause[:-1] + " from " + table_name
    else:
        #indicates the query is for the subsequent sheets - that is the inline questions - so join with main table on the response id and filter on the location values
        sql_query = "select " + columns_clause[:-1] + " from " + table_name + " inner join " + main_table_name + " on  " + table_name + ".response_id = " + main_table_name + ".id "
    # add project ids to where condition if not superuser
    user_project_list = request.session.get('user_project_list') if request.session.get('user_project_list') else []
    if request.user.is_superuser == False and  int(survey_id) not in [70,71,73,181]:
        if len(user_project_list) > 0:
            user_project_list = [str(item) for item in user_project_list]
            where_clause = where_clause + ' and "cluster.project_id"::integer in (' + ','.join(user_project_list) + ')'
        elif len(user_project_list) == 0:
            where_clause = where_clause + ' and false'
    sql_query = sql_query + " where " + where_clause
    return sql_query

def export_excel(request,survey_id, excel_filename,filter_loc_values,date_filter,project_id):
    import csv
    import uuid
    import json
    from django.conf import settings
    from datetime import datetime
    import psycopg2
    conn = None
    writer = None
    try: 
        db_name =  settings.DATABASES['default'].get('NAME')
        username = settings.DATABASES['default'].get('USER')
        password = settings.DATABASES['default'].get('PASSWORD')
        hostname = settings.DATABASES['default'].get('HOST')
        #connect timeout is set to 1 minute (1*60 seconds) = 60
        # TODO: 60 seconds not required, has to be chagned after testing.
        connect_timeout = settings.EXPORT_CSV.get('CONNECT_TIMEOUT_FETCH')
        conn = psycopg2.connect(database=db_name, user=username, password=password, host=hostname, connect_timeout=connect_timeout)
        # conn = connection
        conn.autocommit = True
        conn.set_client_encoding('UTF8')
        conn_str = "postgresql+psycopg2://" + username + ":" + password + "@" + hostname + "/" + db_name + "?client_encoding=UTF8"
        #survey_type used to store survey_type 0 for beneficiary and 1 for activity
        MEDIA_ROOT = settings.MEDIA_ROOT + 'media/temp_export_data/'       
        writer = None
        print(MEDIA_ROOT+excel_filename,'kjke')
        try:
            writer = pandas.ExcelWriter(MEDIA_ROOT+excel_filename,mode='w')
            sql_query = """select meta_info, sheet_names,loc_filter_column_map from export_csv_meta where survey_id = """ + str(survey_id) 
            result = execute_query(conn, sql_query,3)
            meta_info = result[0][0]
            sheet_names = result[0][1]
            loc_filter_column_map = result[0][2]
            data_query = ""
            # filter_values = get_filter_values(request,loc_filter_column_map)
            filter_values = filter_loc_values
            main_table_name = ""
            for loop_index, sheet in enumerate(sheet_names):
                table_name = meta_info[sheet]['tablename']
                columns_list = meta_info[sheet]['excel_columns']
                headers_list = meta_info[sheet]['excel_headers']
                if loop_index == 0:
                    main_table_name = table_name
                rows_in_chunk = 20000
                # % character in the query causing the issue, since % is placeholder in python
                #replaced % from header text with %% to escape the placeholder 
                headers_list_for_query = [i.replace("%",'%%') for i in headers_list]
                # import ipdb;ipdb.set_trace()
                data_query = build_query(request, table_name, columns_list, headers_list_for_query,filter_values,date_filter,main_table_name,survey_id,project_id)
                write_to_excel_from_normalized_table(conn, conn_str, data_query, columns_list,headers_list,rows_in_chunk, sheet, writer)
        finally:
            if writer:
                writer.close()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(str(survey_id)+'---'+error_stack)
        raise
    finally:
        if conn:
            conn.close()


def write_to_excel_from_normalized_table(conn,conn_str, sql_query, columns_list, headers_list, rows_in_chunk, sheetname,excelWriter):
    # read from sql table into the pandas dataframe in chucks, this returns a list of dataframes - one for each chunk
    
    #normalized_df_list = pandas.read_sql_table(table_name, columns=columns_list, con=conn_str, chunksize=rows_in_chunk)
    # print("Conn Str Valiue " , conn_str)
    normalized_df_list = pandas.read_sql_query(sql_query, con=conn_str, chunksize=rows_in_chunk)
    start_row = 0
    header_row_count = 1
    header_info = headers_list

    df_count = 0
    empty_data_msg = 'No Data Found'
    try:
        colname_list = [item[0:63] if len(item) > 63 else item for item in headers_list]
        for chunk_df in normalized_df_list:
            df_count = df_count +1
            if 'Activity Date' in colname_list:
                chunk_df['Activity Date'] = pandas.to_datetime(chunk_df['Activity Date'],format="%d-%m-%Y", errors='coerce').dt.date
            chunk_df.to_excel(excelWriter, sheet_name=sheetname, startrow = start_row, startcol = 0, header=header_info, columns=colname_list)
            # add the dataframe size (rows read from table/ chunk size) and header rows count (1 for first iteration and 0 for further iterations)
            #import ipdb;ipdb.set_trace()
            start_row = start_row + chunk_df.shape[0] + header_row_count
            # set flags to indicate first dataframe is written to excel
            # set header row count used in the calcuation of start row to 0 as no further header rows will be added 
            header_row_count = 0
            # unset flag for header info to false as no further header details will be written to sheet
            header_info = False
    except Exception as e:
        df_count = 0
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(error_stack)
        raise
    # finally:
    #     try:
    #         # drop the temporary table created
    #         sql_query = " DROP TABLE " + table_name
    #         execute_query(conn, sql_query,6)
    #     except Exception as ex1:
    #         exc_type, exc_value, exc_traceback = sys.exc_info()
    #         error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
    #         logger.error(error_stack)
    #create empty sheet if no data
    if df_count  == 0:
        chunk_df = pandas.DataFrame(columns=columns_list)
        chunk_df.to_excel(excelWriter, sheet_name=sheetname, header=header_info, columns=columns_list, encoding='utf-8')