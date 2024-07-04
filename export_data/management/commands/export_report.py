from __future__ import unicode_literals
from django.core.management.base import BaseCommand
import psycopg2
import sys, traceback
from django.shortcuts import render 
from datetime import datetime
import os
import logging
import re
#from report_csv.models import *

logger = logging.getLogger(__name__)

def export_report(survey_list):
    from django.conf import settings
    import sys, traceback    
    import psycopg2
    import time
    from datetime import datetime
    conn = None

    db_name = settings.DATABASES['default'].get('NAME')
    username = settings.DATABASES['default'].get('USER')
    password = settings.DATABASES['default'].get('PASSWORD')
    hostname = settings.DATABASES['default'].get('HOST')
    #sleep time between 2 survey export calls
    sleep_time_seconds = settings.EXPORT_CSV.get('SLEEP_TIME_SECONDS')
    #connect timeout is set to 45 minutes (45*60 seconds) = 2700
    connect_timeout = settings.EXPORT_CSV.get('CONNECT_TIMEOUT_BUILD')
    # db_name = 'akrspiuidev_14oct'#'akrspi_dec31'#'akrspi_dec31_ecsv'
    # username = 'akrspiuser'
    # password = 'AkrspiU53R2021'
    # hostname = '142.93.208.26'#'localhost'
    #sleep_time_seconds = 3
    try:
        conn = psycopg2.connect(database=db_name, user=username, password=password, host=hostname, connect_timeout=connect_timeout)
        conn.autocommit = True
        conn.set_client_encoding('UTF8')
        
        if len(survey_list) == 0:
            #sql_query = "select id, name, report_filename from survey_survey where active = 2"
            #TODO : check if active = 0 needs to be picked
            sql_query = "select id, name, report_filename from survey_survey where active != 0"
        else: 
            sql_query = "select id, name, report_filename from survey_survey where id in (" + ','.join([str(i) for i in survey_list]) + ")"
        export_media_root = settings.MEDIA_ROOT + "media/export_data/" 
        result = execute_query(conn,sql_query,3)
        for i in result:
            # summary_obj = None
            try:
                # summary_obj = summary_log.objects.get_or_none(survey_id=i[0])
                # if summary_obj == None:
                #     summary_obj = summary_log.objects.create(survey_id=i[0],created=datetime.now(),modified = datetime.now(),status = 'Started')
                # summary_obj.survey_name = i[1]
                # summary_obj.save()
                #create excel file name 
                # filename format : data_dump_survey_<id>_<yyyymmmddHHMMSS>.xlxs
                now = datetime.now() # current date and time
                timestamp_str = now.strftime("%Y%b%d%H%M%S") 
                filename = str(i[1])
                filename.replace(" ", "_")
                filename=re.sub("[^A-Za-z0–9_]","",filename)
                excel_filename = filename + '_' + timestamp_str
                # summary_obj.excel_filename = excel_filename+'.xlsx'
                excel_filename = excel_filename
                t1 = datetime.now()
                export_excel(i[0], excel_filename)
                t2 = datetime.now()
                time_delta = (t2-t1)
                ##total_milliseconds = time_delta.microseconds / 1000
                logger.info('Export excel for survey - ' + str(i[1]) + ':(' +str(i[0]) + ') - time taken:' + str(time_delta))

                # summary_obj.status = 'Completed'
                # summary_obj.most_recent_error_details = ''
                update_sql_query = "update survey_survey set report_generated=current_timestamp,report_filename ='"+excel_filename+".xlsx' where id="+str(i[0])
                execute_query(conn,update_sql_query,2)
                try:
                    if i[2] and i[2] not in ("", ".", "..", "/"):
                        old_file = export_media_root + i[2]
                        if os.path.isfile(old_file) and os.access(old_file, os.R_OK):
                            os.remove(old_file)
                except Exception as ex:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
                    logger.warn(error_stack)
            except Exception as e:
                # summary_obj.status = 'Failed'
                exc_type, exc_value, exc_traceback = sys.exc_info()
                error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
                logger.error(error_stack)
                # summary_obj.most_recent_error_details = error_stack
            # summary_obj.save()
            time.sleep(sleep_time_seconds)
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(error_stack) 
        print(error_stack)
    finally:
        if conn:
            conn.close()

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
        logger.debug(sql_query)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        if typ == 3 or typ == 4:
            result = cursor.fetchall()
        elif typ == 5:
            result = cursor.fetchone()[0]
        #conn.commit()  
    finally:
        if cursor:
            cursor.close()
    return result

def export_excel(surveyid, excel_filename):
    import csv
    import uuid
    import json
    from django.conf import settings
    from datetime import datetime
    import sys, traceback    
    import psycopg2
    import pandas as pd
    conn = None
    writer = None
    try:
        db_name = settings.DATABASES['default'].get('NAME')
        username = settings.DATABASES['default'].get('USER')
        password = settings.DATABASES['default'].get('PASSWORD')
        hostname = settings.DATABASES['default'].get('HOST')
        # db_name = 'akrspiuidev_14oct'#'akrspi_dec31'#'akrspi_dec31_ecsv'
        # username = 'akrspiuser'
        # password = 'AkrspiU53R2021'
        # hostname = '142.93.208.26'
        #connect timeout is set to 45 minutes (45*60 seconds)
        conn = psycopg2.connect(database=db_name, user=username, password=password, host=hostname, connect_timeout=2700)
        conn.autocommit = True
        conn.set_client_encoding('UTF8')
#        conn_str = "postgresql+psycopg2://" + username + ":" + password + "@" + hostname  + "/" + db_name
        conn_str = "postgresql+psycopg2://" + username + ":" + password + "@" + hostname + "/" + db_name + "?client_encoding=UTF8"
        survey_id = surveyid
        #survey_type used to store survey_type 0 for beneficiary and 1 for activity
        survey_type_query = """select survey_type from survey_survey where id = """ + str(survey_id) 
        survey_type_result = execute_query(conn, survey_type_query,3)
        survey_type = survey_type_result[0][0]
        # for beneificary baseline survey the creation_key needs to be included in the export list
        beneficary_data_addln_columns = ''
        if survey_type == 0:
            beneficary_data_addln_columns = ' creation_key, '
        
        inline_sql = """ select coalesce(array_to_json(array_agg(q_id)),'[]'::json) 
            from (select sq.id as q_id from survey_question as sq 
            inner join survey_block as sb on sq.block_id = sb.id 
            where upper(sq.qtype) = 'IN' and sq.active != 0 and sb.survey_id = """ + str(survey_id) + """) as t """
        query_result = execute_query(conn,inline_sql,3)
        in_type_questions = query_result[0][0]
        logger.debug(in_type_questions)
        
        response_data = 'response'
        #ignore nested jsons for the In Type questions from this export. 
        #In type questions have variable rows of data and hence will be exported as separate csv/sheets in the excel
        for i in in_type_questions:
            response_data = "(" + response_data + " - '" + str(i) + "')"
        sql_query = """select array_to_json(array_agg(row_to_json(t))) from ( select id, """ + beneficary_data_addln_columns  + """ cluster, """ + response_data + """ as response, submission_date, created, modified, user_id from survey_jsonanswer where active != 0 and survey_id = """ + str(survey_id) + """ order by id #@#LIMIT_OFFSET#@#) t """
        #logger.error("sql_query:" + sql_query)

        #Should be set to False if program does not involve partners and default parter is created
        partner_details_required = False
        #beneficiary surveys
        if survey_type == 0:
            #MOSTLY NOT REQUIRED 
            #validations : 2 - Number (integer), 0 (NA), 99 (Datetime) -- date valiation is based on the qtype = 'D'
            #cluster_info_for_survey = {"columns":["cluster.beneficiary_type_id"],"headers":[,"Beneficiary Type ID"]}
            cluster_info_for_survey = {"columns":[],"headers":[], "validations":[]}
            if survey_id == 1:
                response_id_header = "School App ID"
            elif survey_id == 6:
                response_id_header = "Committee App ID"
            elif survey_id == 8:
                response_id_header = "Committee Member App ID"
            elif survey_id == 4:
                response_id_header = "School master App ID"
            else:
                response_id_header = "Response App ID"
            common_info_for_survey = {"columns":["id","creation_key","submission_date","created","modified","user_id"],"headers":[response_id_header, "Beneificary Unique Key", "Submission Date", "Created On", "Modified On", "Created By User ID"],"validations":[1,0,99,99,99,0]}
            cluster_info_for_survey["columns"].extend(["cluster.beneficiary_type_id","cluster.child_reference_id"])
            cluster_info_for_survey["headers"].extend(["Cluster - Beneficiary Type ID","Cluster - Child Reference ID"])
            cluster_info_for_survey["validations"].extend([0,0])            
            #TODO: no logic currently for checking if partner details required
            if partner_details_required == True:
                cluster_info_for_survey["columns"].extend(["cluster.partner_id","cluster.partner_creation_key"])
                cluster_info_for_survey["headers"].extend(["Partner ID","Partner Unique Key"])
                cluster_info_for_survey["validations"].extend([0,0])
        else: 
            #extended activity surveys
            cluster_info_for_survey = {"columns":["cluster.Boundary","cluster.BeneficiaryResponse","cluster.project_id"],"headers":["Boundary", "BeneficiaryResponse", "Project ID"],
                                        "validations":[0,0,1]}
            common_info_for_survey = {  "columns":["id","creation_key","submission_date","created","modified","user_id","active"],
                                        "headers":["Response ID", "Row Unique Key", "Submission Date", "Created On", "Modified On", "Created By User ID","Active"],
                                        "validations":[1,0,99,99,99,0,0]}

        common_columns = common_info_for_survey.get('columns')
        common_headers = common_info_for_survey.get('headers')
        common_validations = common_info_for_survey.get('validations')
        common_columns.extend(cluster_info_for_survey.get('columns'))
        common_headers.extend(cluster_info_for_survey.get('headers'))
        common_validations.extend(cluster_info_for_survey.get('validations'))
        aw_qtype_text_mapping={"1":"School","4":"School Master","6":"Committee","8":"Committee"}
        # fetch resposne column names and header text for all question types except In type (variable grid questions)
        # AW type question column names and headers are separate query with UNION ALL to combine the list with other type of questions
        address_question_text_prefix = """'""" + aw_qtype_text_mapping.get(str(survey_id),'') + """'""" if str(survey_id) in aw_qtype_text_mapping.keys() else "a.text"
        headers_query = """select * from (select concat('response.', a.id, case when gd_rows.id is null then '' else '.' || gd_rows.id::text || '.' end,
                                    case when gd_cols.id is null then '' else gd_cols.id::text end) as column_name,
                                concat(a.text, case when gd_rows.id is null then '' else '--' || gd_rows.text || '.' end, 
                                    case when gd_cols.id is null then '' else gd_cols.text end) as header_name,
                                    coalesce(a.question_order,'0') as code, coalesce(gd_rows.gd_rows_code,'-1') as gd_rows_code, 
                                    coalesce(gd_cols.gd_cols_code,'-1') as gd_cols_code,
                                    (case when gd_rows.id is null and gd_cols.id is null then coalesce(av.validationtype_id,0) 
                                         when gd_cols.id is not null then gd_cols.gd_cols_validation_type_id 
                                         else 0 end) as validation_type_id,
                                    (case when gd_rows.id is null and gd_cols.id is null then a.qtype
                                         when gd_cols.id is not null then gd_cols.qtype 
                                         else '' end) as qtype 
                            from survey_question a
                            inner join survey_block b on a.block_id = b.id and b.survey_id = """ + str(survey_id) + """
                            left outer join survey_questionvalidation av on a.id = av.question_id and av.active = 2 
                            left outer join (select x1.id, x1.text, x1.parent_id, x1.question_order as gd_rows_code,
                                            coalesce(x1v.validationtype_id,0) as gd_rows_validation_type_id, x1.qtype
                                        from survey_question x1
                                        inner join survey_block x2 on x1.block_id = x2.id and x2.survey_id = """ + str(survey_id) + """
                                        left outer join survey_questionvalidation x1v on x1.id = x1v.question_id and x1v.active = 2 
                                        where parent_id is not null
                                        and x1.active != 0 and is_grid = true  order by x2.block_order, x1.question_order
                            ) as gd_rows on gd_rows.parent_id = a.id
                            left outer join (
                                        select x1.id, x1.text, x1.parent_id, x1.question_order as gd_cols_code,
                                            coalesce(x1v.validationtype_id,0) as gd_cols_validation_type_id, x1.qtype
                                        from survey_question x1
                                        inner join survey_block x2 on x1.block_id = x2.id and x2.survey_id = """ + str(survey_id) + """
                                        left outer join survey_questionvalidation x1v on x1.id = x1v.question_id and x1v.active = 2 
                                        where parent_id is not null
                                        and x1.active != 0 and is_grid = false order by x2.block_order, x1.question_order
                            )  as gd_cols on gd_rows.parent_id = gd_cols.parent_id 
                            where a.qtype in ('AI', 'C', 'D', 'GD', 'H', 'R','S','T','TA', 'AF','AP','SM') -- In type is excluded
                            and a.active != 0
                            and a.parent_id is null                             
                            UNION ALL 
                            ( select concat('response.address.1.', a.id, '.',c.code) as column_name, 
                                concat(""" + address_question_text_prefix + """,'--',c.name) as header_name,
                                coalesce(a.question_order,'0') as code, '-1' as gd_rows_code, coalesce(c.code,'-1') as gd_cols_code,
                                 0 as gd_cols_validation_type_id, a.qtype
                                from survey_question a
                                inner join survey_block b on a.block_id = b.id and b.survey_id = """ + str(survey_id) + """
                                inner join application_master_boundarylevel c on true
                                where a.qtype = 'AW' 
                                and a.parent_id is null and a.active !=0 and c.active != 0
                                order by c.code 
                            )) as x order by coalesce(code,'0')::integer, coalesce(gd_rows_code,'-1')::integer, coalesce(gd_cols_code,'-1')::integer ,header_name desc"""
                            # UNION ALL 
                            # ( select concat('response.address.1.', a.id, '.',c.code,'__id__') as column_name, 
                            #     concat(a.text,'--',c.name,' ID') as header_name
                            #     from survey_question a
                            #     inner join survey_block b on a.block_id = b.id and b.survey_id = """ + str(survey_id) + """
                            #     inner join masterdata_boundarylevel c on true
                            #     where a.qtype = 'AW' 
                            #     and a.parent_id is null and a.active !=0
                            #     order by c.code 
                            # ) 
                            # """
        
        #local
        # MEDIA_ROOT ='/home/mahiti/Desktop/AkrspiExportFiles/static/'
        #dev
        #MEDIA_ROOT ='/home/mahiti/AkrspiExportFiles/static/'
        MEDIA_ROOT = settings.MEDIA_ROOT + "/export_data/"

        # Create the directory if it doesn't exist
        os.makedirs(MEDIA_ROOT, exist_ok=True)

        # Define the full path to the Excel file
        excel_file_path = os.path.join(MEDIA_ROOT, excel_filename + '.xlsx')

        # Use the ExcelWriter to write the file
        writer = pd.ExcelWriter(excel_file_path, mode='w', datetime_format='yyyy/mmm/dd')
        print(MEDIA_ROOT,'-----------------')
        # import zipfile
        # with zipfile.ZipFile(MEDIA_ROOT+excel_filename+'.zip', 'w') as zf:
        #     with zf.open(excel_filename+'.xlsx', 'w') as buffer:
        #         with pd.ExcelWriter(buffer) as writer:
        try:
            #Add main survey data dump to the excel as Main sheet
            add_data_to_excel(conn, sql_query, headers_query, common_columns, common_headers, common_validations, writer, 'Main', conn_str, 0,survey_id, survey_type)

            #For each In Type question in the survey add one sheet with the data dump for that variable grids (In type) in the form
            common_info_for_in_type = {"columns":["response_creation_key","response_id","row_id"],
                            "headers":["Row Creation Key", "Response ID", "Row ID"],
                            "validations":[0,0,0]}

            for q_id in in_type_questions:
                #sql_query = """select array_to_json(array_agg(row_to_json(t))) 
                #from ( select sja.id as response_id, x2.key as row_id, x2.value::jsonb as row_data from survey_jsonanswer sja 
                #join jsonb_each_text(response->'""" + str(q_id) + """') as x2 on true where sja.survey_id = """ +  str(survey_id) + """ #@#LIMIT_OFFSET#@# ) t"""
                sql_query = """select array_to_json(array_agg(row_to_json(t))) 
                from ( select sja.id as response_id, sja.creation_key as response_creation_key, x2.key as row_id, x2.value::jsonb as row_data 
                    from (select * from survey_jsonanswer where active !=0 and survey_id="""+str(survey_id)+ """ order by id #@#LIMIT_OFFSET#@#) sja 
                join jsonb_each_text(response->'""" + str(q_id) + """') as x2 on true where sja.survey_id = """ +  str(survey_id) + """  ) t"""
                headers_query = """select concat('row_data.', a.id) as column_name, concat(a.text) as header_name, a.question_order, null as row_code, null as col_code, coalesce(av.validationtype_id,0) as validation_type_id, a.qtype from survey_question a inner join survey_block b on a.block_id = b.id and b.survey_id = """ + str(survey_id) + """ 
                    left outer join survey_questionvalidation av on av.question_id = a.id and av.active = 2 where qtype in ('AI', 'C', 'D', 'H', 'R','S','T','TA','AF','AP','SM') and a.active != 0 and (a.id 
                = """ + str(q_id) + """ or a.parent_id = """ + str(q_id) + """)"""
                # logger.info("in_sql_query:" + sql_query)
                # logger.info("in_header_query:" + headers_query)
                add_data_to_excel(conn, sql_query, headers_query, common_info_for_in_type.get("columns"), common_info_for_in_type.get("headers"), common_info_for_in_type.get("validations"), writer, 'q_'+str(q_id), conn_str, q_id,survey_id, survey_type)
        finally:
            if writer:
                #save the excel file 
                writer.close()
                #writer.close()
            # if buffer:
            #     buffer.close()    
            # if zf:
            #     zf.close()
            
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(str(survey_id)+'---'+error_stack)
        raise
        #add the logger code with stack trace here
    finally:
        if conn:
            conn.close()

# data query should return a single json array with all records
# headers query should return the columns in the format of the normalized json and header text which is combination of the question text delimited with --
# common headers and common columns should be the common columns names and header text to be picked form the data query
def add_data_to_excel(conn, data_query, headers_query, common_columns, common_headers, common_validations, excelWriter, sheetname, conn_str, q_id,survey_id, survey_type):
    from  pandas import json_normalize
    import json
    import uuid
    import copy
    from datetime import datetime
    rows_in_chunk = 20000
    partner_details_required = False
    survey_question_columns_list = []
    survey_question_headers_list = []
    survey_question_validation_list = []
    date_formatted_columns = []
    logger.debug("common_columns:" + ','.join(common_columns))
    logger.debug("common_headers:" + ','.join(common_headers))
    logger.debug("common_valiations:" + ','.join([str(i) for i in common_validations]))
    #if survey_id == 471:
    #    rows_in_chunk = 1
    #id = uuid.uuid1()
    #rand_str = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
    now = datetime.now() # current date and time
    timestamp_str = now.strftime("%H%M%S")
    table_name = "export_csv_" + str(survey_id)+"_"+ str(q_id)+'_temp'
    # fetch the data specific column names and headers and add these to the common columns and headers list
    # column names - response.<question id> for non grid type questions
    # column names - response.<column question id>.<row question id> for  grid type questions
    #try:
    headers_result = execute_query(conn,headers_query,3)
    columns_list = copy.deepcopy(common_columns)
    headers_list = copy.deepcopy(common_headers)
    validation_list = [i_val for i_val in common_validations]

    
    for i in headers_result:
        col_str = i[0]
        survey_question_columns_list.append(col_str)
        survey_question_headers_list.append(i[1])
        if i[6] == 'D' :
            logger.info(i[0] + ":" + str(i[6]))       
            date_formatted_columns.append(col_str)
            survey_question_validation_list.append(5)
        elif i[6] == 'T':
            survey_question_validation_list.append(i[5])
        else:
            survey_question_validation_list.append(0)
        logger.debug(col_str + " : " + i[6] + "-" + str(i[5]) + "-" + str(survey_question_validation_list[-1]))
    temp_table_primary_key = 'id'
    # Survey specific questions for the beneificary codes 
    ben_type_query = """select config->0->>'object_id_1'::text as ben_type_id 
                        from survey_survey where id = """ + str(survey_id) + """ 
                        and config->0->>'content_type_1'::text = 'BeneficiaryType'"""
    result = execute_query(conn, ben_type_query, 3)
    #import ipdb; ipdb.set_trace()
    logger.debug(result)
    ben_type = '0'
    ben_type_columns_list = []
    ben_type_headers_list = []
    ben_type_validations_list = []
    ai_columns_list = []
    ai_headers_list = []
    ai_validations_list = []
    loc_filter_only_id_columns = []
    loc_filter_only_id_headers = []
    loc_filter_only_id_validations = []
    location_filters_columns_names = {}
    if len(result) == 1:
        ben_type = result[0][0]
    logger.debug('ben_type:' + str(ben_type))
    if q_id != 0:
        temp_table_primary_key = 'response_creation_key, row_id'
    else:
        ## additional columns to fetch names/readable values for code and ids
        if 'user_id' in columns_list:
            columns_list.extend(['user_id_ref_name','user_id_ref_username'])
            headers_list.extend(['Created By User','Created By Username'])
            validation_list.extend([0,0])
        if 'cluster.BeneficiaryResponse' in columns_list:
            columns_list.append('cluster.beneficiary_type_ref_name')
            headers_list.append('Beneficiary Type Name')
            validation_list.append(0)
        if 'cluster.partner_id' in columns_list:
            columns_list.append('cluster.partner_id_ref_name')
            headers_list.append('Partner Name')
            validation_list.append(0)
            partner_details_required = True
        if 'cluster.Boundary' in columns_list:
            boundary_levels_query = "select id, name from application_master_boundarylevel where active != 0 order by code "
            boundarylevel_result = execute_query(conn, boundary_levels_query,3)
            columns_list.append('cluster.boundary_level')
            headers_list.append('Boundary Level')
            validation_list.append(0)
            for boundary in boundarylevel_result:
                if survey_type != 0 and ben_type == '0':
                    columns_list.append('cluster.boundary_'+str(boundary[1]).lower())
                    headers_list.append(str(boundary[1]))
                    validation_list.append(0)
                    location_filters_columns_names.update({boundary[0]:'cluster.boundary_'+str(boundary[1]).lower()})
                    loc_filter_only_id_columns.append('address.'+str(boundary[0])+'__id__')
                    loc_filter_only_id_headers.append(str(boundary[1] + ' ID '))
                    loc_filter_only_id_validations.append(0)
        #beneficiary surveys add the beneficiary ID column
        if survey_type == 0:
            ben_type_columns_list = ['ben.id']
            ben_type_headers_list = ['Beneficiary ID']
            ben_type_validations_list = [0]
            if survey_id == 1: 
                #School - survey_id 1
                #School - Address questions for filter 
                loc_filter_only_id_columns = ['address.1__id__','address.2__id__']
                loc_filter_only_id_headers = ['School - State','School - District']
                loc_filter_only_id_validations = [0,0]
            elif survey_id == 2: 
                #Student - survey_id 2
                #Student - Address questions for filter 
                loc_filter_only_id_columns = ['address.1__id__','address.2__id__']
                loc_filter_only_id_headers = ['Student - State','Student - District']
                loc_filter_only_id_validations = [0,0,0,0,0,0]
            # if survey_id == 6: 
            #     #Committee - survey_id 6
            #     #Committee - Address questions for filter 
            #     loc_filter_only_id_columns = ['address.1__id__','address.2__id__','address.3__id__','address.4__id__', 'address.5__id__','address.6__id__']
            #     loc_filter_only_id_headers = ['Committee - State','Committee - District','Committee - Block','Committee - Ward','Committee - Gram Panchayat','Committee - Village']
            #     loc_filter_only_id_validations = [0,0,0,0,0,0]
            # elif survey_id == 4: 
            #     #School Master - survey_id 4
            #     #School Master - Address questions for filter 
            #     loc_filter_only_id_columns = ['address.1__id__','address.2__id__','address.3__id__','address.4__id__', 'address.5__id__','address.6__id__']
            #     loc_filter_only_id_headers = ['School Master - State','School Master - District','School Master - Block','School Master - Ward','School Master - Gram Panchayat','School Master - Village']
            #     loc_filter_only_id_validations = [0,0,0,0,0,0]
            # elif survey_id == 8: 
            #     #Committee members - survey_id 8
            #     #fetch the Committee details for the Committee members survey
            #     ai_columns_list = ['parent_ben.json_id']
            #     ai_headers_list = ['Committee App ID']
            #     ai_validations_list = [1,0,0]
            #     #Committee members - Address questions for filter 
            #     loc_filter_only_id_columns = ['address.1__id__','address.2__id__','address.3__id__','address.4__id__', 'address.5__id__', 'address.6__id__']
            #     loc_filter_only_id_headers = ['Committee - State','Committee - District','Committee - Block','Committee - Ward','Committee - Gram Panchayat','Committee - Village']
            #     loc_filter_only_id_validations = [0,0,0,0,0,0]
            
        else:
            # #for extended activity surveys
            #  ben_type_id |                 name                  | id 
            # -------------+---------------------------------------+----
            #  2           | Follow up                             |  7
            #  2           | Referral Management                   |  5
            #  2           | Call Management for referred children |  9
            #  2           | Secondary Screening                   |  4
            #  2           | Spectacle Compliance                  |  8
            #  3           | Teacher’s training                    | 10
            #  2           | Primary screening                     |  3
            #  2           | Surgery Detail                        |  6

            if ben_type == '2':
                #student
                loc_filter_only_id_columns = ['address.1__id__','address.2__id__']
                loc_filter_only_id_headers = ['Student - State','Student - District']
                loc_filter_only_id_validations = [0,0]
                ben_type_columns_list = ['ben.json_id', 'ben_type_question.234.1', 'ben_type_question.234.2','ben_type_question.238', 'ben_type_question.241', 'ben_type_question.242', 'ben_type_question.243', 'ben_type_question.240']
                ben_type_headers_list = ['Student App ID', 'Student - State','Student - District','Student - Name of the Student', 'Student - Class/Division', 'Student - Roll number', 'Student - Parents phone number', 'Student - Gender']
                ben_type_validations_list = [1,0,0,0,0,0,0,0]
            elif ben_type == '3':
                #School 
                loc_filter_only_id_columns = ['address.1__id__','address.2__id__']
                loc_filter_only_id_headers = ['School - State','School - District']
                loc_filter_only_id_validations = [0,0]
                ben_type_columns_list = ['ben.json_id', 'ben_type_question.234.1', 'ben_type_question.234.2', 'ben_type_question.231']
                ben_type_headers_list = ['School App ID', 'School - State','School - District','School name']
                ben_type_validations_list = [1,0,0,0]
        #mark the column names to be used for location based filters
        #ensure the columns are added from 1 - 8 in the list
        # if loc_q_num != ""        
        #     for loc_index in [1:9]
        #         location_filters_columns_names.update({loc_index:'ben_type_question.'+ loc_q_num + '.'+str(loc_index)})
        for loop_idx, filter_column_name in enumerate(loc_filter_only_id_columns):
            location_filters_columns_names.update({loop_idx+1:filter_column_name})

        columns_list.extend(ai_columns_list)
        headers_list.extend(ai_headers_list)
        validation_list.extend(ai_validations_list)
        columns_list.extend(ben_type_columns_list)
        headers_list.extend(ben_type_headers_list)
        validation_list.extend(ben_type_validations_list)

    #adding the actual survey question at the end of the list
    columns_list.extend(survey_question_columns_list)
    headers_list.extend(survey_question_headers_list)
    validation_list.extend(survey_question_validation_list)
    
    # logger.debug("columns_list:" + ','.join(columns_list))
    # logger.debug("headers_list:" + ','.join(headers_list))
    # logger.debug("validation_list:" + ','.join([str(i) for i in validation_list]))
    #create temporary table with normalized structure and load survey data 
    t1 = datetime.now()
    create_nomalized_table_load_data(conn, survey_id,data_query, columns_list, validation_list, conn_str, table_name, rows_in_chunk, temp_table_primary_key, loc_filter_only_id_columns, loc_filter_only_id_validations)
    t2 = datetime.now()
    time_delta = (t2-t1)
    #total_milliseconds = time_delta.microseconds / 1000
    logger.info('create_nomalized_table_load_data for survey - ' + str(survey_id) + ':(' +str(q_id) + ') - time taken:' + str(time_delta))
    #execute the sql funtion to replace all ids with text
    # values replaced - choice id to text for single select(S), radio(R), multiselect(C) type questions and boundary ids in address widget (AW)
    str_partner_details_required = 'true' if partner_details_required else 'false'
    #TODO: Uncomment after updating the function
    sql_query = """select replace_ids_with_text(""" + str(survey_id) + """, """ + str(q_id) + """, '""" + table_name + """', """ + str_partner_details_required + """, """ + str(survey_type) + """, """ + str(ben_type) + """) """
    logger.info(sql_query)
    t1 = datetime.now()
    log_result = execute_query(conn, sql_query,4)
    t2 = datetime.now()
    time_delta = (t2-t1)
    #total_milliseconds = time_delta.microseconds / 1000
    logger.info('replace_ids_with_text for survey - ' + str(survey_id) + ':(' +str(q_id) + ') - time taken:' + str(time_delta))
    logger.info('+++++++ start dump of db function log +++++++')
    
    try:
        logger.info(log_result[0][0])
    except Exception:
        logger.error("error reading result:"+ str(log_result))
        #print(log_result)
    logger.info('------ end dump of db function log ---------')
    #store metadata into the export_csv_meta table for using in queries
    #location_filters_columns_names
    modified_header_list = []
    for i in headers_list:
        # header = i.replace("""\""","""\""")
        header = i.replace("'", "\''")
        modified_header_list.append(header)
    excel_headers = []
    excel_columns = []
    # logger.error("columns_list:"+str(columns_list))
    general_cols_list = ["id","row_id","submission_date","created","modified","response_id", 'user_id_ref_name','address.1__id__','address.2__id__','address.3__id__','address.4__id__', 'address.5__id__','address.6__id__']
    for  idx, col in enumerate(columns_list):
        if col in general_cols_list  or col.startswith('response.') or (col.startswith('ben.') and col != 'ben.id')  or col.startswith('ai_') or col.startswith('ben_type_question') or col.startswith('row_data.'):
            excel_columns.append(col)
            excel_headers.append(modified_header_list[idx])
    if q_id == 0:
        meta_sql_query = """delete from export_csv_meta where survey_id = """ + str(survey_id) 
        execute_query(conn, meta_sql_query,2)
        # insert into export_csv_meta(survey_id, sheet_names, meta_info)
        # values(1, array_to_json('{"sheet1"}'::varchar[]),'{"sheet1":{"tablename":"export_csv_1_0_temp","header":["header 1","header 2","header 3"], "columns":["col1","col2","col3"]}}'::JSONB)
        #('{\"""" + sheetname + """\":{"tablename":\"""" + table_name + """\","headers":[\"""" + '","'.join(modified_header_list) + """\"], "columns":[\"""" + '","'.join(columns_list) + """\"]}}'::JSONB),
        #logger.error("general_cols_list:"+str(general_cols_list))
        #logger.error("excel_columns:"+str(excel_columns))
        meta_sql_query = """insert into export_csv_meta(survey_id, sheet_names, meta_info, loc_filter_column_map)
                    values(""" + str(survey_id) + """, array_to_json('{\"""" + sheetname + """\"}'::varchar[]),
                    ('{\"""" + sheetname + """\":{"tablename":\"""" + table_name + """\","headers":[\"""" + '","'.join(modified_header_list) + """\"], "columns":[\"""" + '","'.join(columns_list) + """\"],"excel_headers":[\"""" + '","'.join(excel_headers) + """\"], "excel_columns":[\"""" + '","'.join(excel_columns) + """\"]}}'::JSONB),
                    ('""" + json.dumps(location_filters_columns_names) + """')::JSONB )"""

        execute_query(conn, meta_sql_query,1)
    else:
        # update export_csv_meta 
        # set sheet_names = (sheet_names::jsonb || '["sheet2"]'::jsonb)::json,
        # meta_info = jsonb_set(meta_info,'{sheet2}', '{"tablename":"export_csv_1_100_temp","header":["h1","h2","h3"], "columns":["c1","c2","c3"]}'::JSONB , true)
        # where survey_id = 1
        meta_sql_query = """update export_csv_meta 
                            set sheet_names = (sheet_names::jsonb || '[\"""" + sheetname + """\"]'::jsonb)::json,
                            meta_info = jsonb_set(meta_info,'{""" + sheetname  + """}', '{"tablename":\"""" + table_name + """\","headers":[\"""" + '","'.join(modified_header_list) + """\"], "columns":[\"""" + '","'.join(columns_list)  + """\"],"excel_headers":[\"""" + '","'.join(excel_headers) + """\"], "excel_columns":[\"""" + '","'.join(excel_columns)  + """\"]}'::JSONB , true)
                            where survey_id = """ + str(survey_id)
        #print('meta1',meta_sql_query)
        execute_query(conn, meta_sql_query,2)

    #read data from the normalized table and write to excel sheet
    t1 = datetime.now()
    write_to_excel_from_normalized_table(conn,conn_str, table_name, columns_list, headers_list, validation_list, date_formatted_columns, rows_in_chunk, sheetname,excelWriter, survey_type)
    t2 = datetime.now()
    time_delta = (t2-t1)
    #total_milliseconds = time_delta.microseconds / 1000
    logger.info('write_to_excel_from_normalized_table for survey - ' + str(table_name) + ':(' +str(sheetname) + ') - time taken:' + str(time_delta))
    #finally:
    #    if df:
    #        del df    

#create temporary table with normalized structure and load survey data 
def create_nomalized_table_load_data(conn, survey_id,data_query ,columns_list, validation_list, conn_str, table_name, rows_in_chunk, temp_table_primary_key, loc_filter_only_id_columns,loc_filter_only_id_validations):
    import json
    import d6tstack
    import pandas
    from pandas import json_normalize
    # create a temp table to load normalized data    
    # temp_tables_columns = ['sl_no']
    # temp_tables_columns.extend(columns_list)
    full_columns_list = []
    full_validation_list = []
    full_columns_list.extend(columns_list)
    full_columns_list.extend(loc_filter_only_id_columns)
    full_validation_list.extend(validation_list)
    full_validation_list.extend(loc_filter_only_id_validations)

    create_temp_table(conn, survey_id, table_name, full_columns_list, full_validation_list, temp_table_primary_key)
    #fetch the data from the survey_jsonanswer table
    # this query will be all questions except for In type questions for specific survey 
    # OR the id (Response id) column and all rows from the specific in type question only.
    #data_result = execute_query(conn,data_query)
    limit = rows_in_chunk
    offset_counter = 0
    while True:
        limit_offset_query = ' limit ' + str(limit) + ' offset ' + str(offset_counter * limit) + ' '
        sql_query_with_limit = data_query.replace('#@#LIMIT_OFFSET#@#',limit_offset_query)
        logger.debug(offset_counter)
        logger.debug(sql_query_with_limit)
        t1 = datetime.now()
        data_result = execute_query(conn,sql_query_with_limit,3)
        offset_counter = offset_counter + 1
        t2 = datetime.now()
        time_delta = (t2-t1)
        #total_milliseconds = time_delta.microseconds / 1000
        logger.info('load data execute_query for survey - ' + str(survey_id) + ':(' +str(offset_counter) + ') - time taken:' + str(time_delta))
        df = None
        result_dump = []
        data = []
        if data_result[0][0] is None:
            break
        else:        
            result_dump = json.dumps(data_result[0][0])
            data = json.loads(result_dump)
            ## we can change this flow to load in chunks as well. 
            #import ipdb;ipdb.set_trace()            
            t1 = datetime.now()
            temp_df = json_normalize(data)
            t2 = datetime.now()
            time_delta = (t2-t1)
            #total_milliseconds = time_delta.microseconds / 1000
            logger.info('json_normalize for survey - ' + str(survey_id) + ':(' +str(offset_counter) + ') - time taken:' + str(time_delta))

            #import ipdb;ipdb.set_trace()
#            temp_df.replace(to_replace=[r"\\n", "\n"], value=["",""], regex=True, inplace=True)
            ######## temporary workaround ##############
            # some integer fields are getting chagned to decimal with a .0 to the integer value in json_normalize. 
            # we had a issue of cluster.project_id being converted to decimal 149 was stored as 149.0 in the dataframe.
            ##############
            #START - COMMENTED FOR FURTHER CHANGES FOR OTHER PROJECTS
            # project app/concept removed for this project
            # if 'cluster.project_id' in columns_list:
            #     temp_df['cluster.project_id'] = temp_df['cluster.project_id'].astype(object).apply(lambda x: '%.f' % x)
            #     temp_df['cluster.project_id'] = temp_df['cluster.project_id'].astype(object).replace('Nan', 0)
            #     temp_df['cluster.project_id'] = temp_df['cluster.project_id'].astype(object).replace('nan', 0)
            #     temp_df['cluster.project_id'] = temp_df['cluster.project_id'].astype(object).replace('NaN', 0)
            #     #returns none as the inplace value is set to True
            #     temp_df['cluster.project_id'].astype(object).replace(regex={r'NaN': 0, r"Nan": 0,r'nan':0}, inplace=True)
            #END - COMMENTED FOR FURTHER CHANGES FOR OTHER PROJECTS
            #to convert string dates to date fields to store in the exprot
                # COMMENTED TO ensure the reports and dashboard queries are updated to 
                # handle date type questions as date fields and not char fields 
            # logger.info('full_columns_list:'+ str(full_columns_list))
            # logger.info('full_validation_list:'+ str(full_validation_list))
            temp_df.replace(regex={r'\t': '', r"'": "''",r'Nan':'',r'NaN': 0,r'nan':0,r'\n':'',r'\r':'',r'\\':''}, inplace=True)
            temp_df = temp_df.reindex(columns=full_columns_list,fill_value='')
            for idx, col_name in enumerate(full_columns_list):
                # logger.info("idx:"+str(idx))
                # date fields chagne format -- 5 is qtype 'D'
                if full_validation_list[idx] == 5:
                    temp_df[col_name] = pandas.to_datetime(temp_df[col_name],format='%d-%m-%Y', errors='coerce')
                    #temp_df[col_name] = temp_df[col_name].dt.strftime('%Y-%b-%d')
                    #logger.info("temp_df[col_name] - " + str(col_name) + ": " + str(temp_df[col_name].head(2).tolist()))
            df = temp_df.reindex(columns=full_columns_list,fill_value='')
            #separator is specified as \t, if any textual data has \t, it will pd_to_sql will fail
            #so replaced all \t with ''
            #import ipdb;ipdb.set_trace()
            t1 = datetime.now()
            d6tstack.utils.pd_to_psql(df, conn_str, table_name,if_exists='append', sep='\t')
            t2 = datetime.now()
            time_delta = (t2-t1)
            #total_milliseconds = time_delta.microseconds / 1000
            logger.info('d6tstack.utils.pd_to_psql for survey - ' + str(survey_id) + ':(' +str(offset_counter) + ') - time taken:' + str(time_delta))

            if len(data_result[0][0])<limit:
                break
    index_col_list = []
    if "cluster.BeneficiaryResponse" in full_columns_list:
        index_col_list.append(["cluster.BeneficiaryResponse"])
    if "creation_key" in full_columns_list:
        index_col_list.append(["creation_key"])
    create_table_index(conn, table_name,index_col_list)

# function to create index for the given table name and list of index columns list 
# used for creating the indexes for the export_csv tables
def create_table_index(conn, table_name,index_col_list):
    for index,item in enumerate(index_col_list):
        try:
            cols = '","'.join(item)
            sql_query = "CREATE INDEX " + table_name + "_idx" + str(index) + " on " + table_name + '("' + cols + '")'
            execute_query(conn,sql_query,6)
        except Exception as et: 
            print(table_name+" - create index failed - " + sql_query)
            logger.error(table_name+" - create index failed - " + sql_query)

def create_temp_table(conn, survey_id,table_name,columns_list, validation_list, primary_key):
    # create a table with columns same as the export columns list
    # push the dataframe data to this table 
    # run functions to replace choice IDs with text and address widget boundary ids with names
    # dump the updated data to excel file
#    temp_tables_columns = ['sl_no']
#    temp_tables_columns.extend(columns_list)
    #import ipdb;ipdb.set_trace()
    try:
        #truncate_query = "truncate table "+table_name
        truncate_query = "drop table if exists "+table_name
        execute_query(conn, truncate_query,6)
    except Exception as et:
        logger.error(table_name+" - truncate/drop failed")
    #meta data table with json having all details about a particlar survey. Details include- table names, header list, column list
    #{sheet_name:{"table_name":"","header":[], "columns":[]}}
    #Example for say survey_id 15: {"sheet_name1":{"tablename":"export_csv_15_0_temp","header":[], "columns":[]}, "sheet_name2":{"tablename":"export_csv_15_123_temp","header":[], "columns":[]}} 
    create_meta_data_table = """CREATE TABLE IF NOT EXISTS export_csv_meta(
                                    survey_id int PRIMARY KEY,
                                    meta_info JSONB DEFAULT '{}'::jsonb,
                                    sheet_names JSON DEFAULT '[]'::json,
                                    loc_filter_column_map JSONB DEFAULT '{}'::jsonb
                            )"""
    logger.debug(create_meta_data_table)
    try:
        execute_query(conn, create_meta_data_table,6)
    except Exception as e:
        logger.error('Exception in Create Meta data table - '+ str(e) )
        raise                            
    create_table_query = """ CREATE TABLE IF NOT EXISTS """ + table_name + """ ( """
    for idx, col in enumerate(columns_list):
        col_name = '"'+col+'"'#.replace('.','_')
        #if col_name in  ['"id"', '"response_id"', '"row_id"', '"cluster.project_id"', '"user_id"']:
        # logger.debug("--------col_name:" + col_name + " : " + str(validation_list[idx]))
        if col_name in  ['"id"', '"response_id"', '"row_id"', '"user_id"']:
            field = str(col_name) + ' bigint,'
        elif col_name.endswith('__id__"'):
            field = str(col_name) + ' bigint null DEFAULT 0,'
        elif validation_list[idx] == 1 :
            field = str(col_name) + ' float8 null DEFAULT 0.0,'
        elif validation_list[idx] == 2 :
            field = str(col_name) + ' bigint  DEFAULT 0,'
        elif validation_list[idx] == 5:    
            field = str(col_name) + ' date null,'
        elif validation_list[idx] == 99 or col_name in ['"submission_date"', '"created"', '"modified"']:
            #changed to timestamp without time zone
            #with timezone give a value error while writing to excel (pandas dataframe to_excel)
            #ValueError: Excel does not support datetimes with timezones. Please ensure that datetimes are timezone unaware before writing to Excel
            field = str(col_name) + ' timestamp without time zone null,'
        # elif col_name in ['"submission_date"', '"created"', '"modified"']:
        #     #changed to timestamp without time zone
        #     #with timezone give a value error while writing to excel (pandas dataframe to_excel)
        #     #ValueError: Excel does not support datetimes with timezones. Please ensure that datetimes are timezone unaware before writing to Excel
        #     field = str(col_name) + ' timestamp without time zone,'
        else: 
            field = str(col_name) + ' varchar(5000),'
        create_table_query = create_table_query + field
    create_table_query = create_table_query + ' PRIMARY KEY(' + primary_key+ '))'
    logger.debug(create_table_query)
    try:
        execute_query(conn, create_table_query,6)
    except Exception as e:
        logger.error('Exception in Create table - '+ str(e) )
        raise

def remove_unwanted_key_columns(columns, headers, validations, date_formatted_columns, survey_type):
    #"response.7948" is the AI question. not required as we are not showing any uuids in the excel
    unwanted_columns = ["user_id", "cluster.partner_id","cluster.partner_creation_key", "cluster.active","cluster.Boundary","cluster.BeneficiaryResponse", "cluster.beneficiary_type_id",
                        "cluster.beneficiary_type_ref_name", "cluster.partner_id_ref_name", "cluster.boundary_level","ben.id", "cluster.child_reference_id",
                        "ben_type_question.2","response.7948","creation_key"]
    
    #survey_type
    updated_columns = []
    updated_headers = []
    updated_validations = []
    updated_date_formatted  = []
    # logger.error("columns:" + str(columns))
    # logger.error("validations:" + str(validations))
    for idx, col_name in enumerate(columns):
        if col_name not in unwanted_columns:
            updated_columns.append(col_name)
            updated_headers.append(headers[idx])
            updated_validations.append(validations[idx])
            if col_name in date_formatted_columns:
                updated_date_formatted.append(col_name)
    return updated_columns, updated_headers, updated_validations, updated_date_formatted

import pytz
#read data from the normalized table and write to excel sheet
def write_to_excel_from_normalized_table(conn,conn_str, table_name, columns, headers, validations, date_formatted_columns  , rows_in_chunk, sheetname,excelWriter, survey_type):
    # read from sql table into the pandas dataframe in chucks, this returns a list of dataframes - one for each chunk
    import pandas
    
    columns_list, headers_list, valdiation_list, date_formatted_columns = remove_unwanted_key_columns(columns, headers, validations, date_formatted_columns, survey_type)
    normalized_df_list = pandas.read_sql_table(table_name, columns=columns_list, con=conn_str, chunksize=rows_in_chunk)
    start_row = 0
    header_row_count = 1
    header_info = headers_list
    df_count = 0
    empty_data_msg = 'No Data Found'
    try:
        for chunk_df in normalized_df_list:
            #index_range = range((df_count*(rows_in_chunk)) + 1,((df_count+1)*(rows_in_chunk)) + 1)
            df_count = df_count + 1
            # if 'submission_date' in columns_list:
            #     # print(pandas.to_datetime(chunk_df['submission_date']))
            #     chunk_df["submission_date"] = pandas.to_datetime(chunk_df['submission_date'],errors='coerce', format='%Y/%m/%d')
            # logger.error("date_formatted_columns:" + str(date_formatted_columns))
            # for dt_col in date_formatted_columns:
            #     chunk_df[dt_col] = pandas.to_datetime(chunk_df[dt_col],format='%d-%m-%Y')
            #     chunk_df[dt_col] = chunk_df[dt_col].dt.strftime('%Y-%b-%d')
            #     logger.error("chunk_df[dt_col] - " + str(dt_col) + ": " + str(chunk_df[dt_col].head(2).tolist()))
            # chunk_df=chunk_df.dropna()
            # TODO: not working - need to debug
            #chunk_df.set_index(chunk_df.Index(index_range))
            chunk_df.to_excel(excelWriter, engine='openpyxl', sheet_name=sheetname, startrow = start_row, startcol = 0, header=header_info, columns=columns_list, index =False)
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
        chunk_df.to_excel(excelWriter, sheet_name=sheetname, header=header_info, columns=columns_list)

class Command(BaseCommand):
    import logging
    help = 'Displays current time'
    def add_arguments(self, parser):
        # Optional argument
        parser.add_argument('-s', '--survey_list', type=int, nargs='+'  )
           
    def handle(self, *args, **kwargs):
        survey_list = []
        if kwargs.get('survey_list'):
            survey_list = kwargs.get('survey_list')
        t1 = datetime.now() 
        export_report(survey_list)
        t2 = datetime.now()
        time_delta = (t2-t1)
        #total_milliseconds = time_delta.microseconds / 1000
        logger.info('Total Time Taken:' + str(time_delta))
        
