import os
from django.conf import settings
import pandas as pd
import traceback
import sys
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.db import connection
from .models import ReportMeta
from dashboard.models import DashboardSummaryLog
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from dateutil.relativedelta import relativedelta
import copy
import json
import re
import csv
import logging
from application_master.models import Mission,Project,Donor,Partner,MissionIndicator,MissionIndicatorCategory,UserPartnerMapping,UserProjectMapping,ProjectDonorMapping
from django.contrib.auth.models import User
from datetime import datetime as dt

logger = logging.getLogger(__name__)
# ****************************************************************************
# execute Raw SQL
# ****************************************************************************


def return_sql_results(sql):
    """
    Executes an SQL query and returns the result rows.
    """
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    return rows


# ****************************************************************************
# Excel function for export
# ****************************************************************************


def write_to_excel_from_normalized_table(conn_str, sql_query, headers_list, custom_export_header, rows_in_chunk, sheetname, excelWriter):
    # read from sql table into the pandas dataframe in chucks, this returns a list of dataframes - one for each chunk

    # create headers rows and write to excel sheet
    header_row_count = 1
    row_data = {}
    if custom_export_header:
        # custom export header is used to add custom header info - mostly multi level headers like the child classification report
        for i in custom_export_header:
            row_data.update({tuple(i): {}})
        header_row_count = len(custom_export_header[0])
        header_df = pd.DataFrame.from_dict(row_data)
    else:
        # when custom export header is None, then add the report headers as the export excel headers
        col_list = []
        for i in headers_list[0]:
            # remove any <br/> added in the header as formatting on the html pages
            header_text = i.get('label', '').replace('<br/>', '')
            headers_text = header_text.replace("%",'%%')
            col_list.append(header_text)
        header_df = pd.DataFrame([], columns=col_list)
        header_row_count = 1
        sql_query = sql_query.replace("%",'%%')
    normalized_df_list = pd.read_sql_query(
        sql_query, con=conn_str, chunksize=rows_in_chunk)
    start_row = header_row_count
    # set header to False indicating not to add the header data/row
    header_info = False
    df_count = 0
    try:
        for chunk_df in normalized_df_list:
            chunk_df.index += (df_count * rows_in_chunk)+1
            df_count = df_count + 1
            chunk_df.to_excel(excelWriter, sheet_name=sheetname,
                              startrow=start_row, header=header_info)
            # add the dataframe size (rows read from table/ chunk size) and header rows count (1 for first iteration and 0 for further iterations)
            start_row = start_row + chunk_df.shape[0] #+ header_row_count
            # set flags to indicate first dataframe is written to excel
            # set header row count used in the calcuation of start row to 0 as no further header rows will be added
            header_row_count = 0
            # unset flag for header info to false as no further header details will be written to sheet
            header_info = False

        # add the header row rowas at row 0 - insert it as a new data frame with empty data and the header rows
        header_df.to_excel(excelWriter, sheet_name=sheetname,
                           startrow=0)
    except Exception as e:
        df_count = 0
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(
            exc_type, exc_value, exc_traceback))
        logger.error(error_stack)
        raise

@ login_required(login_url='/login/')
def reports_listing(request):
    """
    View function to render the reports listing page.
    """
    heading='Reports'
    page_reports = ReportMeta.objects.filter(active=2).order_by('display_order')
    return render(request, 'reports/reports.html', locals())
    

@ login_required(login_url='/login/')
def custom_report(request, page_slug):
    rows_per_page = 10
    if request.method == "POST":
        req_data = request.POST
    elif request.method == "GET":
        req_data = request.GET
    mat_view_last_updated = DashboardSummaryLog.objects.get(
        active=2, log_key='mat_partner_mission_meta_view').last_successful_update
    export_flag = True if req_data.get('export') and req_data.get(
        'export').lower() == 'true' else False
    # order of reports is specified in the ReportMeta default ordering
    # page_reports = get_list_or_404(ReportMeta, page_slug=page_slug, active=2)
    page_reports = ReportMeta.objects.filter(
        page_slug=page_slug, active=2).order_by('display_order')
    # temp veriable
    data_query_list = []
    #report_tabs = []
    section_title = []
    table_header = []
    custom_export_headers = []
    total_header_cols = []
    report_slug_list = []
    data = []
    nowrap_cols = []
    user_sort_field = []
    user_sort_order = []
    page_info = []
    sorting_field = []
    user_location_data = None
    filter_values = None

    # get user selected filter data and merge with the user configured location heirarcy
    for idx, report in enumerate(page_reports):
        r_slug = report.report_slug
        s_title = report.report_title
        f_info = report.filter_info
        s_info = report.sort_info
        r_query = report.report_query
        d_query = r_query['sql_query']
        c_query = r_query['count_query'] if r_query['count_query'] else ''
        nw_cols = r_query['nowrap_cols']
        mission_id = r_query['mission_id']
        headers = report.report_header
        e_header = report.custom_export_header
        # all filter settings are set based on the first report filters
        if idx == 0:
            page_slug = report.page_slug
            user_location_data, filter_values, user_filter_values, extended_filter_dict = get_filter_data(
                request, req_data, f_info,mission_id)
        # update any variable_location_names  - in query, count query, sort and headers
        default_sort = r_query['default_sort'] if 'default_sort' in r_query else None


        headers, e_header, data_query, count_query, s_info, default_sort = apply_variable_location_info(
            headers, e_header, d_query, c_query, s_info, default_sort, user_filter_values, user_location_data)

        sort_field, sort_order = set_sort_options(
            req_data, idx, s_info, default_sort)
        user_sort_field.append(sort_field)
        user_sort_order.append(sort_order)

        # page reloads on click of filter, so current page is always set to 1
        current_page = 1
        data_query, count_query = apply_filters_to_query(
            data_query, count_query, f_info, sort_field, sort_order, user_filter_values, current_page, rows_per_page, extended_filter_dict, export_flag)
        # table header details
        table_header.append(headers)
        # get total columns count (colspan sum) - used to display the no records found row
        header_col_count = 0
        for item in headers[0]:
            colspan = item.get('colspan', 0)
            header_col_count += colspan if colspan > 0 else 1

        data_query_list.append(data_query)
        
        if request.method == "POST" and request.POST.get("filter"):
            data.append(return_sql_results(data_query))
        print(data_query)

        total_header_cols.append(header_col_count)
        report_slug_list.append(r_slug)
        custom_export_headers.append(e_header)
        section_title.append(s_title)
        nowrap_cols.append(nw_cols)
        sorting_field.append(s_info)

        # if not for export, prepare pagination details
        if export_flag == False:
            # fetch record count and calcualte pagination info
            total_records = 0
            count_result=None
            if request.method == "POST" and request.POST.get("filter"):
                count_result = return_sql_results(count_query)
            if count_result:
                total_records = count_result[0][0]
            p_info = calculate_pagination_info(total_records, 1, rows_per_page)
            page_info.append(p_info)
            # pagination_range will be same for all reports in the page
            pagination_range = range(p_info.get(
                'start_page'), p_info.get('end_page')+1)
    sidebar_active = 'Report'
    heading = section_title[0]
    # if export button click, create excel and return as response
    if export_flag == True:
        return generate_export_excel(section_title[0], data_query_list, table_header, custom_export_headers, section_title)
    return render(request, 'reports/multitab_report.html', locals())


def generate_export_excel(report_title, data_query_list, table_headers, custom_export_headers, sheet_names):
    from django.conf import settings
    excelWriter = None
    try:
        # Excel path
        rows_in_chunk = 20000
        db_name = settings.DATABASES['default'].get('NAME')
        username = settings.DATABASES['default'].get('USER')
        password = settings.DATABASES['default'].get('PASSWORD')
        hostname = settings.DATABASES['default'].get('HOST')
        # IMPORTANT : Please ensure @ not used in the username and password. This will affect the connection string
        conn_str = "postgresql+psycopg2://" + username + ":" + password + \
            "@" + hostname + "/" + db_name + "?client_encoding=UTF8"
        MEDIA_ROOT = str(settings.MEDIA_ROOT) + '/temp_export_data/'
        import datetime
        file_name = re.sub("(\s)|(')|(-)", '_', report_title)
        folder_file_name = file_name + "_" + \
            datetime.datetime.today().strftime("%d%m%y%H%M%S%f") + ".xlsx"
        attachment_name = file_name + "_" + \
            datetime.datetime.today().strftime("%d%m%y%H%M") + ".xlsx"
        excelWriter = pd.ExcelWriter(MEDIA_ROOT+folder_file_name, mode='w')
        for idx, sql_query in enumerate(data_query_list):
            # sheetname is limited to 30 chars othewise excel gives an error while opening
            write_to_excel_from_normalized_table(
                conn_str, sql_query, table_headers[idx], custom_export_headers[idx], rows_in_chunk, sheet_names[idx][0:30], excelWriter)

    finally:
        if excelWriter:
            excelWriter.close()

    if os.path.exists(MEDIA_ROOT+folder_file_name):
        excel = open(MEDIA_ROOT+folder_file_name, "rb")
        data = excel.read()
        response = HttpResponse(
            data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=%s' % attachment_name
        os.remove(MEDIA_ROOT+folder_file_name)
        return response


def get_loc_filter_value(user_filter_value, user_location_data_value):
    """
    Returns the location filter value based on the provided user filter value and user location data value. 
    """
    loc_id = ''
    if user_filter_value != '':
        loc_id = user_filter_value
    elif user_location_data_value != 0:
        loc_id = str(user_location_data_value)
    return loc_id


def update_location_data_with_user_filter(model, loc_data_index, selected_loc_id, user_location_data):
    """
    Updates the user location data with the selected location ID and model-specific data.
    """
    loc_data = user_location_data[loc_data_index]
    if loc_data[2] == False:
        if model == MissionIndicatorCategory:
            loc_list = list(MissionIndicatorCategory.objects.filter(
                active=2).values_list('id', 'name').order_by('name'))
            loc_data[4].update({str(0): loc_list})
        elif model == MissionIndicator and user_location_data[1][0] != '0':
            loc_list = list(MissionIndicator.objects.filter(
                category_id=user_location_data[0][0], active=2).values_list('id', 'name').order_by('name'))
            loc_data[4].update({str(user_location_data[0][0]): loc_list})
    user_location_data[loc_data_index] = loc_data
    user_location_data[loc_data_index][0] = int(
        selected_loc_id) if selected_loc_id != '' else 0
    return user_location_data


def get_filter_data(request, req_data, f_info,mission_id):
    import dateutil.relativedelta
    filter_values = []
    quarter_month_mapper = {"1": 4, "2": 4, "3": 4, "4": 1, "5": 1,
                            "6": 1, "7": 2, "8": 2, "9": 2, "10": 3, "11": 3, "12": 3}
    current_month = dt.now().strftime('%Y%-m')
    current_qtr = quarter_month_mapper.get(current_month[4:])
    current_year = int(current_month[0:4])
    current_year = current_year - 1 if current_qtr == 4 else current_year
    extended_filters_dict = {}
    # prepare the filter values with fixed order - state, district, shelter and rest of the filters added at the end
    filter_display_order = -1
    f_labels = f_info['filter_labels']
    filter_keys = f_info['filter_labels'].keys()
    user_filter_values = {}
    display_order = f_info['display_order']
    for key in filter_keys:
        str_val = req_data.get(key, '')
        if key == 'start_month':
            str_val=str_val.replace('-','')
        elif key == 'fv_start_month_year':
            str_val=str_val.replace('-','')
        elif key == 'fv_end_month_year':
            str_val=str_val.replace('-','')
        elif key == 'fv_month_year' :
            if str_val == '':
                previous_month=dt.now() + dateutil.relativedelta.relativedelta(months=-1)
                previous_year_month=previous_month.strftime('%Y%-m')
                current_filtered_qtr = quarter_month_mapper.get(previous_year_month[4:])
                selected_year = int(previous_year_month[0:4])
                selected_year = selected_year - 1 if current_filtered_qtr == 4 else selected_year
                str_val=previous_month.strftime('%Y%#m')
            else:
                str_val=str_val.replace('-','')
                current_filtered_qtr = quarter_month_mapper.get(str_val[4:].lstrip('0'))
                selected_year = int(str_val[0:4])
                selected_year = selected_year - 1 if current_filtered_qtr == 4 else selected_year
            user_filter_values.update({'fv_fy_start_month_year': str(selected_year)+'04'})
            user_filter_values.update({'fv_fy_year': str(selected_year)})
        elif request.method == 'POST' and key == 'partner' and str_val == '' :
            str_val=str(request.session['user_partner_list'])[1:-1]
        elif request.method == 'POST' and key == 'project' and str_val == '' :
            str_val=str(request.session['user_project_list'])[1:-1]
        user_filter_values.update({key: str_val})
    user_location_data = request.session['user_location_data'] if 'user_location_data' in request.session else None
    if user_location_data == None:
        load_user_details_to_sessions(request)
        user_location_data = request.session['user_location_data']
    user_location_data = copy.deepcopy(user_location_data)
    category_id = get_loc_filter_value(user_filter_values.get(
        'category', ''), user_location_data[0][0])
    indicator_id = get_loc_filter_value(user_filter_values.get(
        'indicator', ''), user_location_data[1][0])
    
    user_location_data = update_location_data_with_user_filter(
        MissionIndicatorCategory, 0, category_id, user_location_data)
    user_location_data = update_location_data_with_user_filter(
        MissionIndicator, 1, indicator_id, user_location_data)
    user_location_dict = request.session['user_location_dict'] if 'user_location_dict' in request.session else None
    loc_data = None
    for i in display_order:
        filter_values.append([])
    for k in filter_keys:
        data_list = []
        filter_display_order = -1
        if k in display_order:
            filter_display_order = display_order.index(k)

        if k == 'donor':
            donor_list = Donor.objects.filter(id__in=request.session['user_donor_list'],active=2).values_list('id', 'name')
            data_list = [(str(item[0]), item[1])
                         for item in donor_list]
            data_id = user_filter_values.get('donor', '')
            filter_type = 'select'
        elif k == 'partner':
            partner_list = Partner.objects.filter(id__in=request.session['user_partner_list'],active=2).values_list('id', 'name')
            data_list = [(str(item[0]), item[1])
                         for item in partner_list]
            data_id = user_filter_values.get('partner', '')
            filter_type = 'select'
        elif k == 'project':
            project_list = Project.objects.filter(id__in=request.session['user_project_list'],partner_mission_mapping__mission_id=mission_id,active=2).values_list('id', 'name')
            data_list = [(str(item[0]), item[1])
                         for item in project_list]
            data_id = user_filter_values.get('project', '')
            filter_type = 'select'
        elif k == 'category':
            loc_data = user_location_data[0][4]
            data_id = str(user_location_data[0][0])
            data_list = loc_data.get('0', [])
            if (data_id == '0' or len(data_list) == 1) and user_location_data[0][2] == True:
                query_data_id = user_location_dict.get('category', [])
                query_data_id = ','.join([str(i) for i in query_data_id])
                user_filter_values.update({'category': query_data_id})
            filter_type = 'select'
        elif k == 'indicator':
            loc_data = user_location_data[1][4]
            data_id = str(user_location_data[1][0])
            state_id = str(user_location_data[0][0])
            data_list = loc_data.get(state_id, [])
            if (data_id == '0' or len(data_list) == 1) and user_location_data[1][2] == True:
                query_data_id = user_location_dict.get('indicator', [])
                query_data_id = ','.join([str(i) for i in query_data_id])
                user_filter_values.update({'indicator': query_data_id})
            filter_type = 'select'
        elif k == 'start_month':
            data_list = []
            data_id = user_filter_values.get('start_month', '')
            if data_id != '':
                data_id='-'.join([data_id[:4],data_id[4:6]])
            filter_type = 'month'
        elif k == 'fv_month_year':
            data_list = []
            data_id = user_filter_values.get('fv_month_year') if user_filter_values.get('fv_month_year') != '' else current_month
            if data_id != '' and '-' not in data_id:
                data_id='-'.join([data_id[:4],data_id[4:6]])
            filter_type = 'month'
        elif k == 'fv_start_month_year':
            data_list = []
            data_id = user_filter_values.get('fv_start_month_year') 
            if data_id != '':
                data_id='-'.join([data_id[:4],data_id[4:6]])
            filter_type = 'month'
        elif k == 'fv_end_month_year':
            data_list = []
            data_id = user_filter_values.get('fv_end_month_year') 
            if data_id != '':
                data_id='-'.join([data_id[:4],data_id[4:6]])
            filter_type = 'month'
        elif k == 'grading':
            data_list = [(" A ", " A "), (" B ", " B "), (" C "," C "), (" D ", " D "), (" E ", " E "),(" O ", " O ")]
            data_id = user_filter_values.get('grading', '')
            
            filter_type = 'select'
        elif k == 'case_worker_qtr_start':
            data_list = [("202102", "FY'21 Q2"), ("202103", "FY'21 Q3"), ("202104",
                                                                          "FY'21 Q4"), ("202201", "FY'22 Q1"), ("202202", "FY'22 Q2")]
            data_id = user_filter_values.get('case_worker_qtr_start', '')
            data_id = str(current_year*100 +
                          current_qtr) if data_id == '' else data_id
            filter_type = 'select'
            qtr_end = user_filter_values.get('case_worker_qtr_end', '')
            qtr_end = str(current_year*100 +
                          current_qtr) if qtr_end == '' else qtr_end
            extended_filters_dict = add_extended_filters(data_id, qtr_end)
        elif k == 'case_worker_qtr_end':
            data_list = [("202102", "FY'21 Q2"), ("202103", "FY'21 Q3"), ("202104",
                                                                          "FY'21 Q4"), ("202201", "FY'22 Q1"), ("202202", "FY'22 Q2")]
            data_id = user_filter_values.get('case_worker_qtr_end', '')
            data_id = str(current_year*100 +
                          current_qtr) if data_id == '' else data_id
            filter_type = 'select'
        if filter_display_order == -1:
            filter_values.append(
                [k, data_list, data_id, f_labels.get(k, ''), filter_type])
        else:
            filter_values[filter_display_order] = [
                k, data_list, data_id, f_labels.get(k, ''), filter_type]

    return user_location_data, filter_values, user_filter_values, extended_filters_dict


def add_extended_filters(qtr_start, qtr_end):
    import datetime
    qtr_start_months = {"1": 4, "2": 7, "3": 10, "4": 1}
    qtr_end_months = {"1": 6, "2": 9, "3": 12, "4": 3}
    extended_filters_dict = {}
    fy_start_year = qtr_start[:4]
    start_qtr = int(qtr_start[-2:])
    end_qtr = int(qtr_end[-2:])
    qtr_start_month = qtr_start_months.get(str(start_qtr))
    fy_start_year = int(fy_start_year) + \
        1 if qtr_start_month == 1 else int(fy_start_year)
    fy_end_year = int(qtr_end[:4])
    qtr_end_month = qtr_end_months.get(str(end_qtr))
    # generate the list of quearters to be included as per the start and end quarters
    qtr_range = []
    sq = start_qtr
    cy = fy_start_year
    while True:
        for i in range(sq, 5):
            qtr_range.append(str(cy*100+i))
            if cy == fy_end_year and i >= end_qtr:
                break
        if cy < fy_end_year:
            cy = cy + 1
            sq = 1
        else:
            break
    qtr_range_str = ''
    for idx, i in enumerate(qtr_range):
        if idx >= 1:
            qtr_range_str = qtr_range_str + ","
        qtr_range_str = qtr_range_str + "'" + i + "'"
    
    # caluclate the end and start months to be used in the query
    fy_end_year = int(
        fy_end_year) + 1 if qtr_end_month == 3 else int(fy_end_year)
    filter_start_date = str(fy_start_year)+"-" + \
        str(qtr_start_month).rjust(2, '0')+"-01"
    filter_end_date = str(fy_end_year)+"-" + \
        str(qtr_end_month).rjust(2, '0')+"-01"
    filter_end_date = datetime.datetime.strptime(filter_end_date, '%Y-%m-%d')
    filter_end_date = filter_end_date + relativedelta(months=1)
    filter_end_date = filter_end_date.strftime('%Y-%m-%d')
    qtr_range = []

    extended_filters_dict.update({'case_worker_qtr_ext_filter': """ and (case_worker_start_date < '""" + filter_end_date + """'::date 
                                and (case_worker_pause_date is null or case_worker_pause_date >= '""" + filter_start_date + """'::date)
                                and (case_worker_end_date is null 
                                    or case_worker_end_date >= '""" + filter_start_date + """'::date)
                                )"""})
    extended_filters_dict.update({'qtr_range_ext_filter': qtr_range_str})
    return extended_filters_dict


def update_variable_sort_details(sort_info, default_sort, location_name, location_filter, const_variable_location_name):
    # update sort info
    updated_sort_info = {}
    # update default sort
    if default_sort:
        default_sort_field = default_sort.get('sort_field', '')
        default_sort.update({'sort_field': default_sort_field.replace(
            const_variable_location_name, location_name)})
    return default_sort, updated_sort_info


def apply_variable_location_info(header, custom_export_header, data_query, count_query, sort_info, default_sort, user_filter_values, user_location_data):
    location_name = ''
    const_variable_location_name = '@@variable_location_name'
    location_filter = ''

    # update custom export header
    if custom_export_header:
        for row_idx, row in enumerate(custom_export_header):
            for col_idx, item in enumerate(row):
                if item == const_variable_location_name:
                    custom_export_header[row_idx][col_idx] = location_filter

    # update header data
    for row in header:
        for col in row:
            col_label = col.get('label')
            if col_label == const_variable_location_name:
                col_label = col_label.replace(
                    const_variable_location_name, location_filter)
                col.update({'label': col_label})
    default_sort, sort_info = update_variable_sort_details(
        sort_info, default_sort, location_name, location_filter, const_variable_location_name)
    # update data and count queries
    data_query = data_query.replace(
        const_variable_location_name, location_name)
    count_query = count_query.replace(
        const_variable_location_name, location_name)
    return header, custom_export_header, data_query, count_query, sort_info, default_sort


def set_sort_options(req_data, idx, s_info, default_sort):
    sort_field = req_data.get('sort_field_'+str(idx), '')
    sort_order = req_data.get('sort_order_'+str(idx), 'asc')
    # set the default sort order if configured in the report_query section - key : default_sort and value is a dict with sort_order and sort_fields
    # "default_sort":{"sort_field":"classification","sort_order":"asc"}
    if default_sort:
        if 'sort_field' in default_sort and sort_field == '':
            sort_field = default_sort.get('sort_field', '')
        if 'sort_order ' in default_sort and sort_field == '':
            sort_order = default_sort.get('sort_order', 'asc')
    elif sort_field == '':
        # when default sort not specified, set the sort field to first key in the list and order to asc
        for key in s_info:
            sort_field = s_info.get(key, '')
            sort_order = 'asc'
            break
    return sort_field, sort_order


def apply_filters_to_query(data_query, count_query, filter_info, sort_field, sort_order, user_filter_values, current_page, rows_per_page, extended_filter_dict, export_flag):
    # apply filters and sort conditions to query
    filter_cond = filter_info['filter_cond']
    # IMPORTANT - Please cast all timezone aware timestamp fields to timestamps without timezone in the query
    # or use the to_char function and pass required format
    for key in filter_cond.keys():
        filter_value = user_filter_values.get(key)
        updated_cond = ''
        if filter_value != None and filter_value != '' and filter_value != '0':
            f_cond = filter_cond[key]
            if f_cond.lower().replace(' ','').find("in(@@filter_value)") == -1:
                updated_cond = filter_cond[key].replace('@@filter_value',filter_value)
            else:
                updated_cond = filter_cond[key].replace(
                    '@@filter_value', filter_value)
        data_query = data_query.replace('@@'+key+'_filter', updated_cond)
        count_query = count_query.replace('@@'+key+'_filter', updated_cond)
    # apply extended filters dict
    for f_key, f_value in extended_filter_dict.items():
        data_query = data_query.replace('@@'+f_key, f_value)
        count_query = count_query.replace('@@'+f_key, f_value)
    limits_query = ''
    if export_flag is None or export_flag == False:
        limits_query = ' LIMIT ' + \
            str(rows_per_page) + ' OFFSET ' + \
            str(rows_per_page*(current_page-1))
    else:
        data_query = data_query.replace('<br/>', '')
    data_query = data_query.replace('@@LIMITS', limits_query)

    sortings = ''
    if sort_field != None and sort_field != '':
        sort_order = '' if sort_order == None else sort_order
        sortings = ' order by ' + sort_field + ' ' + sort_order + ' '
    data_query = data_query.replace('@@sortings', sortings)
    return data_query, count_query


def calculate_pagination_info(total_records, current_page, rows_per_page):
    display_page_range = 10
    num_pages = int(total_records/rows_per_page)
    num_pages = num_pages if total_records % rows_per_page == 0 else num_pages + 1
    start_page = (current_page - int(display_page_range/2))
    start_page = 1 if start_page < 1 else start_page
    end_page = start_page + display_page_range - 1
    end_page = num_pages if end_page > num_pages else end_page
    first_row = ((current_page-1)*rows_per_page) + 1
    last_row = (current_page*rows_per_page)
    last_row = total_records if last_row > total_records else last_row
    dicta = {"rec_count": total_records, "current_page": current_page, "rows_per_page": rows_per_page, "display_page_range": display_page_range,
             "num_pages": num_pages, "start_page": start_page, "end_page": end_page, "first_row": first_row, "last_row": last_row}
    return {"rec_count": total_records, "current_page": current_page, "rows_per_page": rows_per_page, "display_page_range": display_page_range,
            "num_pages": num_pages, "start_page": start_page, "end_page": end_page, "first_row": first_row, "last_row": last_row}


@ login_required(login_url='/login/')
def custom_report_reload(request, page_slug, report_slug):
    import sys
    import traceback
    html = ''
    rows_per_page = 10
    try:
        if request.method == 'POST' and request.is_ajax():
            if request.method == "POST":
                req_data = request.POST
            elif request.method == "GET":
                req_data = request.GET

            # order of reports is specified in the ReportMeta default ordering
            # page_reports = get_list_or_404(ReportMeta, page_slug=page_slug, active=2)
            page_reports = ReportMeta.objects.filter(
                page_slug=page_slug, active=2).order_by('display_order')
            table_header = []
            report_slug_list = []
            data = []
            nowrap_cols = []
            user_sort_field = []
            user_sort_order = []
            sorting_field = []
            page_info = []
            user_filter_values = {}
            total_header_cols = []
            report_idx = 0
            for idx, report in enumerate(page_reports):
                if report.report_slug == report_slug:
                    report_idx = idx
                else:
                    continue
                report_slug_list.append(report.report_slug)
                r_query = report.report_query
                d_query = r_query['sql_query']
                c_query = r_query['count_query'] if r_query['count_query'] else ''
                mission_id = r_query['mission_id']
                f_info = report.filter_info
                s_info = report.sort_info
                e_header = report.custom_export_header
                headers = report.report_header  # table_header
                user_location_data, filter_values, user_filter_values, extended_filter_dict = get_filter_data(
                    request, req_data, f_info,mission_id)
                # update any variable_location_names  - in query, count query, sort and headers
                default_sort = r_query['default_sort'] if 'default_sort' in r_query else None
                headers, e_header, data_query, count_query, s_info, default_sort = apply_variable_location_info(
                    headers, e_header, d_query, c_query, s_info, default_sort, user_filter_values, user_location_data)
                sort_field, sort_order = set_sort_options(
                    req_data, report_idx, s_info, default_sort)
                user_sort_field.append(sort_field)
                user_sort_order.append(sort_order)

                current_page = int(req_data.get('page_'+str(report_idx), '0'))
                data_query, count_query = apply_filters_to_query(
                    data_query, count_query, f_info, sort_field, sort_order, user_filter_values, current_page, rows_per_page, extended_filter_dict, False)
                data.append(return_sql_results(data_query))

                # table header details
                table_header.append(headers)
                # get total columns count (colspan sum) - used to display the no records found row
                total_records = int(req_data.get(
                    'rec_count_'+str(report_idx), '0'))
                total_header_cols.append(total_records)

                p_info = calculate_pagination_info(
                    total_records, current_page, rows_per_page)
                pagination_range = range(p_info.get(
                    'start_page'), p_info.get('end_page')+1)
                page_info.append(p_info)
                sorting_field.append(s_info)
            html = render_to_string('reports/report_ajax_reload.html', {"req_data": req_data, "report_idx": report_idx, "table_header": table_header, "data": data,
                                                                        "nowrap_cols": nowrap_cols, "user_sort_field": user_sort_field, "user_sort_order": user_sort_order, "page_info": page_info,
                                                                        "pagination_range": pagination_range})
    except Exception as ex1:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(
            exc_type, exc_value, exc_traceback))
    return HttpResponse(html)


def load_user_details_to_sessions(request):
    # Getting the user role config if not it will raise exception
    # [loc_id, "loc_name", loc_config, {loc_data}]
    # - config True if the location is from user location config, false if its a user selected location from filter dropdown
    # [district_id, "district_name", True, [district_id1, distrit_id2, district_id3], {"state_id":[(district_id1, "district_name1"),(district_id2, "district_name2")]}]
    try:

        # user_role_location_level_config = User.objects.get(
        #     id=request.user.id)
        # user_group = user_role_location_level_config.groups.first()
        # # content type id of the user location level - state/district/shelter
        # location_hierarchy_type_id = user_role_location_level_config.location_hierarchy_type.id
        user_based_categories =request.session['user_category_list']
        loc_ids = user_based_categories
        loc_id = ''
        loc_name = ''
        config_loc = False
        shelter_list, district_list, state_list = [], [], []
        shelter_data, district_data, state_data = {}, {}, {}
        shelter_config, district_config, state_config = False, False, False
        loc_list = MissionIndicatorCategory.objects.filter(id__in=user_based_categories).values_list(
            'id', 'name',).order_by('name')        
        state_config = True
        attrib_len = 2
        for item in loc_list:
            new_state = (item[0], item[1])
            state_list.append(new_state[0])
            s_list = state_data.get('0', [])
            s_list.append(new_state)
            state_data.update({'0': s_list})
            if attrib_len > 2:
                new_district = (item[2], item[3])
                district_list.append(new_district[0])
                district_for_state = district_data.get(str(new_state[0]), [])
                district_for_state.append(new_district)
                district_data.update({str(new_state[0]): district_for_state})
            if attrib_len > 4:
                new_shelter = (item[4], item[5])
                shelter_list.append(new_shelter[0])
                shelter_for_district = shelter_data.get(
                    str(new_district[0]), [])
                shelter_for_district.append(new_shelter)
                shelter_data.update(
                    {str(new_district[0]): shelter_for_district})
        user_location_data = []
        state_list = list(set(state_list))
        district_list = list(set(district_list))
        shelter_list = list(set(shelter_list))
        state_id, state_name = 0, ''
        if len(state_list) == 1:
            state_id = state_list[0]
            state_name = state_list[0]
        for loc_item in state_data:
            state_data.update(
                {loc_item: sorted(list(set(state_data.get(loc_item, []))), key=lambda x: x[1])})
        user_location_data.append(
            [state_id, state_name, state_config, state_list, state_data])
        district_id, district_name = 0, ''
        if len(district_list) == 1:
            district_id = district_list[0]
            district_name = district_list[0]
        for loc_item in district_data:
            district_data.update({loc_item: sorted(
                list(set(district_data.get(loc_item, []))), key=lambda x: x[1])})
        user_location_data.append(
            [district_id, district_name, district_config, district_list, district_data])
        shelter_id, shelter_name = 0, ''
        if len(shelter_list) == 1:
            shelter_id = shelter_list[0]
            shelter_name = shelter_list[0]
        for loc_item in shelter_data:
            shelter_data.update({loc_item: sorted(
                list(set(shelter_data.get(loc_item, []))), key=lambda x: x[1])})
        user_location_data.append(
            [shelter_id, shelter_name, shelter_config, shelter_list, shelter_data])
        user_location_dict = {'state': state_list,
                              'district': district_list, 'shelter': shelter_list}
    except User.DoesNotExist:
        configure_error = 'Username not configured . Please contact administration.'
        return configure_error

    request.session['user_location_data'] = user_location_data
    request.session['user_location_dict'] = user_location_dict


@ login_required(login_url='/login/')
def get_indicator(request):
    if request.method == 'GET' and request.is_ajax():
        selected_category = request.GET.get('selected_category', '')
        user_location_data = request.session['user_location_data'] if 'user_location_data' in request.session else None
        if user_location_data == None:
            load_user_details_to_sessions(request)
            user_location_data = request.session['user_location_data']
        loc_data = user_location_data[1]  # index 1 is category data
        result_set = []
        if loc_data[2] == True:  # user configured districts
            districts = loc_data[4].get(selected_category, [])
        else:  # all indicators for category
            districts = MissionIndicator.objects.filter(category_id=int(
                selected_category), active=2).order_by('name').values_list('id', 'name')
        for district in districts:
            result_set.append(
                {'id': district[0], 'name': district[1], })
        return HttpResponse(json.dumps(result_set))
