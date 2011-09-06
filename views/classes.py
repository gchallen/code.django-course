from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.http import HttpResponse, Http404
from course.models import University, Department, Offering, Semester
from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse

urlpatterns = patterns('course.views.classes',
                       url(r'^/$', 'summary'),
                       url(r'^/summary/$', 'summary', name='summary'),
                       url(r'^/schedule/$', 'schedule', name='schedule'),
                       url(r'^/staff/$', 'staff', name='staff'),
                       url(r'^/assignments/((?P<assignment>\d+)/)?$', 'assignments', name='assignments'))

class MenuLink:
  def __init__(self, name, url, current=False, visible=True):
    self.name = name
    self.url = url
    self.current = current
    self.visible = visible

def loadLinks(theclass, current, visible=None):
  theclass.menulinks = [MenuLink('Summary', reverse('summary')),
                        MenuLink('Schedule', reverse('schedule')),
                        MenuLink('Assignments', reverse('assignments')),
                        MenuLink('Staff', reverse('staff'))]
  for menulink in theclass.menulinks:
    if menulink.name == current:
      menulink.current = True
    if visible != None and menulink.name not in visible:
      menulink.visible = False

def summary(request, theclass):
  loadLinks(theclass, "Summary")
  return render_to_response('class/summary.html',
                            {'theclass': theclass},
                            context_instance=RequestContext(request))

def assignments(request, theclass, assignment=None):
  if assignment == None:
    return render_to_response('class/assignments.html',
                              {'theclass': theclass},
                              context_instance=RequestContext(request))
  else:
    return render_to_response('class/assignment.html',
                              {'theclass': theclass},
                              context_instance=RequestContext(request))

def schedule(request, theclass):
  raise Http404;

def staff(request, theclass):
  raise Http404;
