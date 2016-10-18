import json
import random
from itertools import chain

from django.contrib.auth.models import User
from django.db.models import Model
from django.shortcuts import render
from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .models import Activity, ActivityType, ActivityCategory, ActivityLocation, Participant
from .forms import ActivityForm
from django.template import loader
from django.template.defaulttags import register
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value, CharField, FloatField


# Create your views here.
def index(request):
    # get search 't' - type and 'v' value 
    if 't' in request.GET and 'v' in request.GET:
        filter_type = request.GET['t']
        filter_value = request.GET['v']

        # check possible variation to prevent XSS injection
        if filter_type == 'at':
            result = Activity.objects.filter(activity_type=filter_value)
        elif filter_type == 'ac':
            result = Activity.objects.filter(activity_category=filter_value)
        elif filter_type == 'an':
            result = Activity.objects.annotate(
                similarity=TrigramSimilarity('name', request.GET['search'])
            ).filter(similarity__gt=0.1)
    else:
        result = Activity.objects

    context = {
        'activities': result.all()
    }

    template = loader.get_template('activity/index.html')
    return HttpResponse(template.render(context, request))


def get_hints(request):
    if 'q' not in request.GET:
        return JsonResponse({})

    search = request.GET['q']
    # name__istartswith
    activity_data = Activity.objects.annotate(
        similarity=TrigramSimilarity('name', search),
        f_name=Value('an', output_field=CharField())
    ).filter(similarity__gt=0.1).values('id', 'name', 'similarity', 'f_name')

    activity_type_data = ActivityType.objects.annotate(
        similarity=Value(0.8, output_field=FloatField()),
        f_name=Value('at', output_field=CharField())
    ).filter(name__istartswith=search).values('id', 'name', 'similarity', 'f_name')

    activity_category_data = ActivityCategory.objects.annotate(
        similarity=Value(0.6, output_field=FloatField()),
        f_name=Value('ac', output_field=CharField())
    ).filter(name__istartswith=search).values('id', 'name', 'similarity', 'f_name')

    # Get top most suitable hint by order by similarity
    hints = sorted(chain(activity_data, activity_type_data, activity_category_data),
                   key=lambda x: x['similarity'], reverse=True)

    result = list(hints)

    result_json = json.dumps(result)
    return HttpResponse(result_json, content_type='application/json')


def calcAvailableSpots(activities):
    availableSpots = {}
    for activity in activities:
        availableSpots[activity.id] = activity.participants_limit - Participant.objects.filter(
            activity=activity).count()
    return availableSpots


def create(request):
    if request.user.is_authenticated():
        if request.method == 'GET':
            form = ActivityForm()
        else:
            form = ActivityForm(request.POST)
            if form.is_valid():
                activity = form.save(commit=False)
                activity.organizer = request.user
                activity.save()
                return HttpResponseRedirect(reverse('activity:activity_detail', kwargs={'activity_id': activity.id}))
        return render(request, 'activity/create.html', {'activity_form': form})
    else:
        return HttpResponseRedirect('login/')
        # activity_categories = ActivityCategory.objects.all()
        # activity_types = ActivityType.objects.all()
        # context = {
        #     'activity_categories': activity_categories,
        #     'activity_types': activity_types,
        # }
        # return render(request, 'activity/create.html', context)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


# Delete activity by specified id (passed as get parameter)
def delete(request):
    # redirect to main page if the user is not authenticated
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    # get the ID from the get request
    activity_id = request.GET.get('id')
    try:
        # try to load activity from the database
        activity = Activity.objects.get(id=activity_id)
        # restrict deletion in case if activity does not belong to the user
        if activity.organizer.id != request.user.id:
            return HttpResponse()
        activity.delete()
    except Model.DoesNotExist as e:
        print(e)
    return HttpResponse()


# Dismiss activity by specified activity id and user id (passed as get parameters)
def dismiss(request):
    # redirect to main page if the user is not authenticated
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    activity_id = request.GET.get('activity_id')
    user_id = request.GET.get('user_id')
    # do nothing if there is no valid info in request
    if activity_id is None or user_id is None:
        return HttpResponse()
    try:
        # try to load activity from the database
        activity = Activity.objects.get(id=activity_id)
        user = User.objects.get(id=user_id)
        part_activity = Participant.objects.get(user=user, activity=activity)
        part_activity.delete()
    except Model.DoesNotExist as e:
        print(e)
    return HttpResponse()


def detail(request, activity_id):
    try:
        activity = Activity.objects.get(pk=activity_id)
    except Activity.DoesNotExist:
        raise Http404("The activity your are looking for doesn't exist.")
    return render(request, 'activity/detail.html', {'activity': activity})
