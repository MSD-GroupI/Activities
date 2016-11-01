from django.conf.urls import url
from . import views
from . import statistics


app_name = 'activity'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^activity/create/$', views.create, name='activity_create'),
    url(r'^activity/create/(?P<activity_id>\d+)$', views.create, name='activity_create'),
    url(r'^activity/(?P<activity_id>\d+)/$', views.detail, name='activity_detail'),
    url(r'^activity/edit/(?P<activity_id>\d+)/$', views.edit, name='activity_edit'),
    url(r'^activity/delete', views.delete, name='activity_delete'),
    url(r'^activity/(?P<activity_id>\d+)/dismiss/$', views.dismiss, name='dismiss_activity'),

    url(r'activity/hints/', views.get_hints, name='activity_hints'),

    url(r'activity/join', views.join, name='join_activity'),
    url(r'activity/recommendations$', statistics.recommendations, name='recommendations'),
    url(r'^activity/(?P<activity_id>\d+)/locations/$', views.locations, name='locations'),
    url(r'^activity/(?P<activity_id>\d+)/status/change/(?P<new_status>\S{2})/$', views.change_status, name='change_status'),
    url(r'^activity/(?P<activity_id>\d+)/rating/change/(?P<new_rating>\d+)/$', views.change_rating, name='change_rating'),

]
