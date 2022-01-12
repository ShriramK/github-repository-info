from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect
from social_django.models import UserSocialAuth

import datetime
import json
import requests
import time

from .models import Repos


# Application Url
GITHUB_APP_URL = 'https://fast-peak-45295.herokuapp.com'


def home(request):
    user = request.user
    try:
        github_login = user.social_auth.get(provider='github')
    except Exception:
        github_login = False

    return render(request, 'examples/home.html', {
        'app_url': GITHUB_APP_URL,
        'github_login': github_login,
    })


@login_required
def settings(request):
    user = request.user

    try:
        github_login = user.social_auth.get(provider='github')
    except UserSocialAuth.DoesNotExist:
        github_login = None

    can_disconnect = (user.social_auth.count() >= 1)

    return render(request, 'examples/settings.html', {
        'github_login': github_login,
        'can_disconnect': can_disconnect,
        'app_url': GITHUB_APP_URL
    })


@login_required
def get_repositories(request):
    user = request.user
    try:
        github_login = user.social_auth.get(provider='github')
        response = requests.get(
            'https://api.github.com/users/' +
            github_login.extra_data.get('login')+'/repos'
            )
        repos_data = response.content.decode()
        repos_data = json.JSONDecoder().decode(repos_data)

        repo_user_id = -1
        if repos_data != '':
            repo_user_id = repos_data[0]['owner']['id']
        else:
            # no public repository data
            return JsonResponse({'message': 'No public repository data'})

        # check how long ago it's fetched to do a re-fetch
        recently_fetched_time = datetime.datetime.now()
        recently_fetched_time -= datetime.timedelta(minutes=15)
        recently_fetched_time = time.mktime(recently_fetched_time.timetuple())

        repo_user_id_int = int(repo_user_id)
        repos_obj = None
        try:
            repos_obj = Repos.objects.filter(repo_user_id=repo_user_id_int)
            # if record exists
            if len(repos_obj) > 0:
                if recently_fetched_time < repos_obj[0].fetched_time:
                    return redirect('get_repos_view', repo_user_id)
                else:
                    # clear records
                    delete_repos(repos_obj)
        except Exception:
            # Error in formatting: OperationalError: no such table: examples_repos
            pass

        # get list of repos from above current response
        avatar_url = repos_data[0]['owner']['avatar_url'] \
            if len(repos_data) > 0 else ''

        # process and append
        current_repos_info = extract_repos_info(response)

        # store repository info in db
        repos_obj = Repos()
        repos_obj.repo_names = current_repos_info
        repos_obj.repo_user_id = repo_user_id
        repos_obj.avatar_url = avatar_url
        repos_obj.fetched_time = int(time.time())
        repos_obj.save()

        # retrieve url and num of pages to fetch next set of data

        # get rate_limit info from response headers
        # limit per hour
        rate_limit_rem = int(response.headers['X-RateLimit-Remaining'])

        url_data = response.headers['Link']
        url_data_parts = url_data.split(',')
        url_data_next = ''
        url_data_last = ''
        if 'next' in url_data_parts[0]:
            url_data_next = url_data_parts[0].split(';')
            url_data_last = url_data_parts[1].split(';')
        elif 'next' in url_data_parts[1]:
            url_data_next = url_data_parts[1].split(';')
            url_data_last = url_data_parts[0].split(';')

        next_repo_url = url_data_next[0][1:-1]

        last_repo_url = url_data_last[0][1:-1]
        last_repo_url_parts = last_repo_url.split('?')

        # 'page=<last_page_num>'
        total_pages_data = last_repo_url_parts[1].split('=')

        total_pages_num = int(total_pages_data[1])

        # fetch data in loop
        min_pages = min(total_pages_num, rate_limit_rem)
        page_pos = 2
        while page_pos <= min_pages:
            repos_response = requests.get(next_repo_url)

            more_repos_info = extract_repos_info(repos_response)

            # store data in db
            repos_obj = Repos()
            repos_obj.repo_names = more_repos_info
            repos_obj.repo_user_id = repo_user_id
            repos_obj.avatar_url = avatar_url
            repos_obj.fetched_time = int(time.time())
            repos_obj.save()

            # get new set of data
            next_repo_url = get_next_repos_url(repos_response)
            page_pos += 1

        return redirect('get_repos_view', repo_user_id)
    except UserSocialAuth.DoesNotExist:
        error_info = {'error': 'Github data doesnot exist', 'avatar_url': '',
                      'list_repos': [], 'username': ''}
        return JsonResponse(error_info)
        """return render(request, 'examples/repos.html', error_info)"""


def get_next_repos_url(response):
    url_data = response.headers['Link']
    url_data_parts = url_data.split(',')
    url_data_next = ''
    for each_part in url_data_parts:
        if 'next' in each_part:
            url_data_next = each_part.split(';')
    next_repo_url = '' if url_data_next == '' else url_data_next[0].strip()[1:-1]
    return next_repo_url


def extract_repos_info(response):
    repos_data = response.content.decode()
    list_of_repos = []
    repos_data = json.JSONDecoder().decode(repos_data)
    for each in repos_data:
        list_of_repos.append(each['name'])
    return list_of_repos


def delete_repos(repos_obj=None):
    # empty repos info
    if repos_obj == None:
        repos_obj = Repos.objects.all()
    for each in repos_obj:
        each.delete()


@login_required
def get_repos_view(request, repo_user_id):
    user = request.user
    github_login = user.social_auth.get(provider='github')
    repo_user_id_int = int(repo_user_id)
    repos_data = Repos.objects.filter(repo_user_id=repo_user_id_int)
    paginator = Paginator(repos_data, 1)
    avatar_url = paginator.object_list[0].avatar_url
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    resp_data = {'page_obj': page_obj, 'github_login': github_login,
                 'app_url': GITHUB_APP_URL, 'avatar_url': avatar_url,
                 'repo_user_id': repo_user_id_int}
    return render(request, 'examples/repos.html', resp_data)
