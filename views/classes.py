from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.http import HttpResponse, Http404
from course.models import University, Department, Offering, Semester
from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from datetime import datetime, time

urlpatterns = patterns('course.views.classes',
                       url(r'^/$', 'summary'),
                       url(r'^/summary/$', 'summary', name='summary'),
                       url(r'^/schedule/(?P<ignored>all/)?$', 'scheduleall', name='schedule-all'),
                       url(r'^/schedule/next/$', 'schedulenext', name='schedule-next'),
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
                        MenuLink('Schedule', reverse('schedule-next')),
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
  loadLinks(theclass, "Assignments")
  if assignment == None:
    return render_to_response('class/assignments.html',
                              {'theclass': theclass},
                              context_instance=RequestContext(request))
  else:
    return render_to_response('class/assignment.html',
                              {'theclass': theclass},
                              context_instance=RequestContext(request))

def schedulenext(request, theclass):
  start = datetime.now()
  end = datetime.combine(theclass.semester.end, time())
  return schedule(request, theclass, start, end)

def scheduleall(request, theclass, ignored=True):
  start = datetime.combine(theclass.semester.start, time())
  end = datetime.combine(theclass.semester.end, time())
  return schedule(request, theclass, start, end)

def schedule(request, theclass, start, end):
  loadLinks(theclass, "Schedule")
  meetings = theclass.meeting_set.filter(start__gte=start, end__lte=end)
  return render_to_response('class/schedule.html',
                            {'theclass': theclass,
                             'meetings': meetings},
                            context_instance=RequestContext(request))


def staff(request, theclass):
  raise Http404;
