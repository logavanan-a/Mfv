from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from survey.models import *
# from userroles.models import *

def get_imei_user_id(uid):
    l = ["0","0","0","0","0"]
    x = str(uid)
    l[-len(x):] = [i for i in x]
    return "".join(i for i in l)


def validate_user(view):
    def is_auth(request, *args, **kwargs):
        error_msg, status ,activeStatus= '', False,2
        if request.method == 'POST':
            email = request.POST.get('userId')
            password = request.POST.get('password')
            # from userroles.serializers import user_setup
            '''
                Why this IF condition below?
                *    Login username as case sensitive
                *    Before doing this we should save all the username as lower case
            '''
            # if user_setup().get('login_username_as_casesensitive') == 2:
            email = email.lower()
            # import ipdb; ipdb.set_trace()

            user = authenticate(username=email, password=password)
            if user is None:
                usr=User.objects.filter(username=email)
                if usr and not usr.first().is_active:
                    error_msg = "User is In-active"
                    activeStatus=0
                else:
                    error_msg = "Invalid username or password"
            elif user.is_active:
                login(request, user)
                kwargs['user'] = user
                status = True
            
        kwargs.update({'status':status, 'error_msg':error_msg,'activeStatus':activeStatus})
        return view(request, *args, **kwargs)
    return is_auth



def validate_user_version(view):
    def check_version(request, *args, **kwargs):
        error_msg, status = '', False
        user_id = request.POST.get('uId')
        t_id = request.POST.get('t_id').replace('%2C',',')
        vn = request.POST.get('vn').replace('%2C',',')
        vn = "1.0" if vn == '' else vn
        sids_list = [int(i) for i in t_id.split(',')]
        vns_list = [float(i) for i in vn.split(',')]
        res = dict(zip(sids_list,vns_list))
        for k,v in res.items():
            survey_id, vn = k, v
            userrole = UserRoles.objects.filter(user__id=int(user_id))
            survey_access = DetailedUserSurveyMap.objects.filter(user = \
                                                        userrole,survey__id=int(survey_id)).exists()
            if User.objects.filter(id=int(user_id)).exists() and survey_id:
                version_list = Version.objects.filter(survey__id = int(survey_id))
                status = True
                if len(version_list) >= 1 and float(version_list.latest('id').version_number) == float(vn):
                    kwargs['latestversion'] = version_list.latest('id').version_number
                else:
                    error_msg = "Version mis-match"
            else:
                error_msg = "User doesnot exist or Survey not taged to user"
        kwargs.update({'status':status, 'error_msg':error_msg})
        return view(request, *args, **kwargs)
    return check_version


def validate_post_method(view):
    def check_method(request, *args, **kwargs):
        error_msg, status = '', False
        if request.method != 'POST':
            res = {'message':'Invalid request'}
            return JsonResponse(res)
        return view(request, *args, **kwargs)
    return check_method
