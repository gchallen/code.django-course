from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.http import HttpResponse, Http404
from course.models import University, Department, Offering, Semester
from django.conf.urls.defaults import *

urlpatterns = []
urlpatterns += patterns('course.views.classes',
                        (r'^/$', 'summary'),
                        (r'^/summary/$', 'summary'))

def summary(request, theclass):

  return render_to_response('class/summary.html', 
                           {'theclass': theclass},
                            context_instance=RequestContext(request))
