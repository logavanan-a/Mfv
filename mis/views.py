from __future__ import unicode_literals
# from schedule import every, repeat, run_pending
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.shortcuts import redirect, render

import requests
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
# from child_management.models import *
from django.contrib.auth.models import User, auth
from django.db.models import Subquery
# from master_data.models import *
from django.http import JsonResponse
# from django.db import connection
from django.utils.encoding import smart_str
from datetime import datetime
import csv
from django.core.management import call_command
from django.http import HttpResponseRedirect
# from child_management.views import *     
from django.contrib.sessions.models import Session
   
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
            return redirect('/child-list/')
            # else:
            #     logout(request)
        else:
            error_message = "Invalid Username and Password"
    return render(request, 'login.html', locals())


# @login_required(login_url='/login/')
# @permission_required('child_management.view_child', raise_exception=True)
def child_listing(request):
    heading = "Child Management"
    return render(request, 'mis/child_listing.html', locals())


def guardian_add(request, auto_child_id=None):
    heading = "Add New Guardian"
    if request.method == 'POST':
        data = request.POST

        name = data.get('name')
        contact_number = data.get('phone_number')
        relation = data.get('relationship')
        address = data.get('address')
        child_id = data.get('child')

        if True:
            return redirect('/child-list/')

    return render(request, 'mis/add_child_form.html', locals())