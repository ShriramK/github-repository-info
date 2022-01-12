"""github_repository_info URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, re_path

from github_repository_info.apps.examples import views as examples_views

urlpatterns = [
    re_path(r'^$', examples_views.home, name='home'),
    re_path(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    # re_path(r'accounts/login/$', auth_views.LoginView.as_view(), name='login'),
    # re_path(r'^logout/$', auth_views.auth_logout, name='logout'),
    # re_path(r'^oauth/', include('social_django.urls', namespace='social')),
    # path(r'^oauth/', include('social_django.urls', namespace='social')),
    re_path('', include('social_django.urls', namespace='social')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^settings/$', examples_views.settings, name='settings'),
    re_path(r'repoDataView/(?P<repo_user_id>\d+)', examples_views.get_repos_view, name='get_repos_view'),
    re_path(r'^repos/$', examples_views.get_repositories, name='get_repositories'),
]
