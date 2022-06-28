from __future__ import unicode_literals

import csv
import json
from datetime import datetime

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# from child_management.models import *
from django.contrib.auth.models import User, auth
# from child_management.views import *     
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Subquery
# from master_data.models import *
from django.http import HttpResponseRedirect, JsonResponse
# from schedule import every, repeat, run_pending
from django.shortcuts import (HttpResponse, HttpResponseRedirect, redirect,
                              render)
# from django.db import connection
from django.utils.encoding import smart_str

from .models import *
from application_master.models import *


def login_view(request):
    heading = "Login"
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            findUser = User._default_manager.get(username__iexact=username)
        except User.DoesNotExist:
            findUser = None
        if findUser is not None:
            username = findUser.get_username()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # configure_error = load_user_details_to_sessions(request)
            # if not configure_error:
            return redirect('/mission/list/')
            # else:
            #     logout(request)
        else:
            error_message = "Invalid Username and Password"
    return render(request, 'login.html', locals())

# @login_required(login_url='/login/')
# @permission_required('child_management.view_child', raise_exception=True)
def mission_list(request):
    heading = "Mission List"
    mission_obj = Mission.objects.all()

    return render(request, 'mis/mission_list.html', locals())


def missionindicator_table(request, id):
    mission_obj = Mission.objects.get(id = id)
    heading = mission_obj.name

    mic_obj = MissionIndicatorCategory.objects.filter(mission__id = id)

    if request.method == 'POST':
        data = request.POST
        print(data,'data')


        if True:
            return redirect('/mission/list/')

    return render(request, 'mis/indicator_list.html', locals())

def mission_add(request):
    mi_obj = MissionIndicator.objects.all()
    data = request.POST
    result = []
    for temp in mi_obj:
            one = data.getlist('pro_'+str(temp.id))
            result.append(one)
    print(result)

    return render(request, 'mis/add_child_form.html', locals())

