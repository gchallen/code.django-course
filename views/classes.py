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
                       url(r'^/schedule/$', 'scheduledefault', name='schedule-default'),
                       url(r'^/schedule/next/$', 'schedulenext', name='schedule-next'),
                       url(r'^/schedule/all/$', 'scheduleall', name='schedule-all'),
                       url(r'^/staff/$', 'staff', name='staff'),
                       url(r'^/assignments/((?P<assignment>\d+)/)?$', 'assignments', name='assignments'))

class MenuLink:
  def __init__(self, name, url, current=False, visible=True):
    self.name = name
    self.url = url
    self.current = current
    self.visible = visible

def loadLinks(current, visible=None):
  menulinks = [MenuLink('Summary', reverse('summary')),
               MenuLink('Schedule', reverse('schedule-default')),
               MenuLink('Assignments', reverse('assignments'))]
  return initLinks(menulinks, current, visible)

def initLinks(menulinks, current, visible=None):
  for menulink in menulinks:
    if menulink.name == current:
      menulink.current = True
    if visible != None and menulink.name not in visible:
      menulink.visible = False
  return menulinks

def summary(request, theclass):
  theclass.menulinks = loadLinks("Summary")
  theclass.submenulinks = None
  return render_to_response('class/summary.html',
                            {'theclass': theclass},
                            context_instance=RequestContext(request))

def assignments(request, theclass, assignment=None):
  theclass.menulinks = loadLinks("Assignments")
  theclass.submenulinks = None
  if assignment == None:
    return render_to_response('class/assignments.html',
                              {'theclass': theclass},
                              context_instance=RequestContext(request))
  else:
    return render_to_response('class/assignment.html',
                              {'theclass': theclass},
                              context_instance=RequestContext(request))

def loadScheduleSubLinks(current, visible=None):
  menulinks = [MenuLink('Next', reverse('schedule-next')),
               MenuLink('All', reverse('schedule-all'))]
  return initLinks(menulinks, current, visible)

def scheduledefault(request, theclass):
  start = datetime.now()
  end = datetime.combine(theclass.semester.end, time())
  meetings = theclass.meeting_set.filter(start__gte=start, end__lte=end)
  if len(meetings) > 0:
    return schedulenext(request, theclass)
  else:
    return scheduleall(request, theclass)

def schedulenext(request, theclass):
  start = datetime.now()
  end = datetime.combine(theclass.semester.end, time())
  meetings = theclass.meeting_set.filter(start__gte=start, end__lte=end).order_by('start')
  if len(meetings) > 0:
    meetings[0].nextmeeting = True
  theclass.submenulinks = loadScheduleSubLinks('Next')
  return schedule(request, theclass, meetings)

def scheduleall(request, theclass, ignored=True):
  start = datetime.combine(theclass.semester.start, time())
  end = datetime.combine(theclass.semester.end, time())
  meetings = theclass.meeting_set.filter(start__gte=start, end__lte=end).order_by('start')

  for meeting in meetings:
    if meeting.start > datetime.now():
      meeting.nextmeeting = True
      break

  theclass.submenulinks = loadScheduleSubLinks('All')
  return schedule(request, theclass, meetings)

def schedule(request, theclass, meetings):
  theclass.menulinks = loadLinks("Schedule")
  return render_to_response('class/schedule.html',
                            {'theclass': theclass,
                             'meetings': meetings},
                            context_instance=RequestContext(request))


def staff(request, theclass):
  raise Http404;
