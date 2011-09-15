import urlparse

from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from course.models import University, Department, Offering, Semester, CourseUser
from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from datetime import datetime, time

from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.auth.views import logout as logout_view
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.models import get_current_site
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.sites.models import Site

# 13 Sep 2011 : GWA : TODO : Rename module to class, not classes.

urlpatterns = patterns('course.views.classes',
                       url(r'^/$', 'summary'),
                       url(r'^/summary/$', 'summary', name='summary'),
                       url(r'^/schedule/$', 'scheduledefault', name='schedule-default'),
                       url(r'^/schedule/next/$', 'schedulenext', name='schedule-next'),
                       url(r'^/schedule/all/$', 'scheduleall', name='schedule-all'),
                       url(r'^/staff/$', 'staff', name='staff'),
                       url(r'^/assignments/((?P<assignment>\d+)/)?$', 'assignments', name='assignments'),
                       url(r'^/login/$', 'login', name='login'),
                       url(r'^/logout/$', 'logout', name='logout'),
                       url(r'^/reset/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', 'reset', name='reset'), 
                      )

def getclassuser(request, theclass):
  if not request.user.is_authenticated():
    theclass.classuser = None
    return False
  try:
    classuser = theclass.users.get(user=request.user)
  except CourseUser.DoesNotExist:
    theclass.classuser = None
    return False
  theclass.classuser = classuser
  return True

@csrf_protect
@never_cache
def login(request, theclass, template_name='class/login.html', redirect_field_name=REDIRECT_FIELD_NAME, authentication_form=AuthenticationForm):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
      form = authentication_form(data=request.POST)
      if form.is_valid():
        netloc = urlparse.urlparse(redirect_to)[1]

      # Use default setting if redirect_to is empty
      if not redirect_to:
          redirect_to = settings.LOGIN_REDIRECT_URL

      # Security check -- don't allow redirection to a different
      # host.
      elif netloc and netloc != request.get_host():
          redirect_to = settings.LOGIN_REDIRECT_URL

      # Okay, security checks complete. Log the user in.
      auth_login(request, form.get_user())

      if request.session.test_cookie_worked():
        request.session.delete_test_cookie()

      if not getclassuser(request, theclass):
        current_site = Site.objects.get_current()
        messages.warning(request, 'While you have an account on %s, you are not listed as a member of this class. Please contact <a href="mailto:%s">%s</a> if this is a mistake.' % (current_site.name, theclass.contactemail, theclass.contactemail))
      else:
        # 12 Sep 2011 : GWA : TODO : Fix this to work with styling. Skipping for now.
        # messages.success(request, 'Log on successful.')
        pass

      return HttpResponseRedirect(redirect_to)
    else:
      form = authentication_form(request)

    request.session.set_test_cookie()

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
        'theclass' : theclass,
    }
    theclass.selectedmenulink = 'Login'
    return render_to_response(template_name, context,
                              context_instance=RequestContext(request, current_app=theclass.app_name))

def logout(request, theclass):
  return logout_view(request)

class MenuLink:
  def __init__(self, name, url, current=False, visible=True):
    self.name = name
    self.url = url
    self.visible = visible

def loadLinks(theclass, visible=None):
  menulinks = [MenuLink('Summary', reverse('course:summary')),
               MenuLink('Schedule', reverse('course:schedule-default')),
               MenuLink('Assignments', reverse('course:assignments'))]
  return initLinks(menulinks, visible)

def initLinks(menulinks, visible=None):
  for menulink in menulinks:
    if visible != None and menulink.name not in visible:
      menulink.visible = False
  return menulinks

def summary(request, theclass):
  theclass.menulinks = loadLinks(theclass)
  theclass.selectedmenulink = 'Summary'
  theclass.submenulinks = None
  return render_to_response('class/summary.html',
                            {'theclass': theclass},
                            context_instance=RequestContext(request, current_app=theclass.app_name))

def assignments(request, theclass, assignment=None):
  theclass.menulinks = loadLinks(theclass)
  theclass.selectedmenulink = 'Assignments'
  theclass.submenulinks = None
  if assignment == None:
    return render_to_response('class/assignments.html',
                              {'theclass': theclass},
                              context_instance=RequestContext(request, current_app=theclass.app_name))
  else:
    return render_to_response('class/assignment.html',
                              {'theclass': theclass},
                              context_instance=RequestContext(request, current_app=theclass.app_name))

def loadScheduleSubLinks(visible=None):
  menulinks = [MenuLink('Next', reverse('schedule-next')),
               MenuLink('All', reverse('schedule-all'))]
  return initLinks(menulinks, visible)

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
  meetings = theclass.meeting_set.filter(end__gte=start, end__lte=end).order_by('start')
  if len(meetings) > 0:
    meetings[0].nextmeeting = True
  theclass.submenulinks = loadScheduleSubLinks()
  theclass.selectedsubmenulink = 'Next'
  return schedule(request, theclass, meetings)

def scheduleall(request, theclass, ignored=True):
  start = datetime.combine(theclass.semester.start, time())
  end = datetime.combine(theclass.semester.end, time())
  meetings = theclass.meeting_set.filter(start__gte=start, end__lte=end).order_by('start')

  for meeting in meetings:
    if meeting.end > datetime.now():
      meeting.nextmeeting = True
      break

  theclass.submenulinks = loadScheduleSubLinks()
  theclass.selectedsubmenulink = 'All'
  return schedule(request, theclass, meetings)

def schedule(request, theclass, meetings):
  theclass.menulinks = loadLinks(theclass)
  theclass.selectedmenulink = 'Schedule'
  return render_to_response('class/schedule.html',
                            {'theclass': theclass,
                             'meetings': meetings},
                            context_instance=RequestContext(request, current_app=theclass.app_name))

def staff(request, theclass):
  raise Http404;

def reset(request, theclass, uidb36=None, token=None):
  return password_reset_confirm(request,
                                uidb36,
                                token,
                                template_name='class/password_reset_confirm.html',
                                # 13 Sep 2011 : GWA : TODO : Fix redirect.
                                # post_reset_redirect='',
                                extra_context={'theclass' : theclass})
