import urlparse,logging,random,re

from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from course.models import University, Department, Offering, Semester, CourseUser, Pitch, PitchVote
from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from datetime import datetime, time

from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, authenticate
from django.contrib.auth.views import logout as logout_view, password_reset_confirm
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.models import get_current_site
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.sites.models import Site
from django.utils.http import base36_to_int
from django.contrib.auth.forms import SetPasswordForm

# 13 Sep 2011 : GWA : TODO : Rename module to class, not classes.

urlpatterns = patterns('course.views.classes',
                       url(r'^/$', 'summary'),
                       url(r'^/summary/$', 'summary', name='summary'),
                       url(r'^/schedule/$', 'scheduledefault', name='schedule-default'),
                       url(r'^/schedule/next/$', 'schedulenext', name='schedule-next'),
                       url(r'^/schedule/all/$', 'scheduleall', name='schedule-all'),
                       url(r'^/staff/$', 'staff', name='staff'),
                       # 23 Sep 2011 : GWA : TODO : Gross. Need to make assignments more modular.
                       url(r'^/pitches/$', 'pitchesview', kwargs={'pitchid': None}),
                       url(r'^/pitches/view/$', 'pitchesview', name='pitches-view'),
                       url(r'^/pitches/view/(?P<pitchid>\d+)?$', 'pitchesview', name='pitches-view'),
                       url(r'^/pitches/edit/$', 'pitchesedit', name='pitches-edit'),
                       url(r'^/projects/$', 'projectsviewselected', name='projects-selected'),
                       url(r'^/projects/selected/$', 'projectsviewselected', name='projects-selected'),
                       url(r'^/projects/all/$', 'projectsviewall', name='projects-all'),
                       url(r'^/login/$', 'login', name='login'),
                       url(r'^/logout/$', 'logout', name='logout'),
                       url(r'^/reset/complete/$', 'reset_complete', name='reset-complete'),
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
          redirect_to = reverse('course:summary')

        # Security check -- don't allow redirection to a different
        # host.
        elif netloc and netloc != request.get_host():
          redirect_to = reverse('course:summary')

        # Okay, security checks complete. Log the user in.
        auth_login(request, form.get_user())

        if request.session.test_cookie_worked():
          request.session.delete_test_cookie()

        if not getclassuser(request, theclass):
          current_site = Site.objects.get_current()
          messages.warning(request, 'While you have an account on %s, you are not listed as a member of this class. Please contact <a href="mailto:%s">%s</a> if this is a mistake.' % (current_site.name, theclass.contactemail, theclass.contactemail))
        else:
          messages.success(request, 'Log on successful.')

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
               MenuLink('Projects', reverse('course:projects-selected'))]
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
  menulinks = [MenuLink('Next', reverse('course:schedule-next')),
               MenuLink('All', reverse('course:schedule-all'))]
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
  theclass.resetlinks()
  
  # 21 Sep 2011 : GWA : Stolen from contrib/auth/views.py. Our version also
  #               logs the user in and sends a message on successful password reset.
  
  """
  View that checks the hash in a password reset link and presents a
  form for entering a new password.
  """

  assert uidb36 is not None and token is not None # checked by URLconf

  # 21 Sep 2011 : GWA : On successful reset we log the user in and redirect to the course summary page.

  post_reset_redirect = reverse('course:summary')
  try:
    uid_int = base36_to_int(uidb36)

    # 21 Sep 2011 : GWA : Here we look in the class object to see if this user is a part of this class. Otherwise fail.

    user = theclass.users.get(user__id=uid_int).user

  # 21 Sep 2011 : GWA : Changed this to a general exception; hopefully that's still OK.

  except Exception:
    user = None

  if user is not None and token_generator.check_token(user, token):
      validlink = True
      if request.method == 'POST':
          form = SetPasswordForm(user, request.POST)
          if form.is_valid():
              form.save()
              user = authenticate(username=user.username, password=form.cleaned_data['new_password1'])
              auth_login(request, user)

              if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
              
              messages.success(request, "Your password has been reset successfully. You are now logged in.")

              return HttpResponseRedirect(post_reset_redirect)
      else:

          # 21 Sep 2011 : GWA : Added so that we can log user in above.

          request.session.set_test_cookie()
          form = SetPasswordForm(None)
  else:
      validlink = False
      form = None
  context = {
      'form': form,
      'validlink': validlink,
  }
  context.update({'theclass' : theclass})
  return render_to_response('class/reset/confirm.html',
                            context,
                            context_instance=RequestContext(request, current_app=theclass.app_name))

def reset_complete(request, theclass):
  theclass.resetlinks()
  return render_to_response('class/reset/complete.html',
                            context_instance=RequestContext(request, current_app=theclass.app_name))

# 23 Sep 2011 : GWA : TODO : Pitch assignment-specific code. Needs to be modularized.

# 23 Sep 2011 : GWA : TODO ; Form stuff should also go somewhere else.

from django import forms

class PitchForm(forms.Form):
  title = forms.CharField(max_length=1024)
  description = forms.CharField(widget=forms.Textarea)
  youtubeID = forms.SlugField(max_length=32, required=False)

class PitchVoteForm(forms.Form):
  
  def __init__(self, *args, **kwargs):
    pitchids = kwargs.pop('pitchids')
    try:
      votes = kwargs.pop('votes')
    except:
      votes = {}
    super(PitchVoteForm, self).__init__(*args, **kwargs)
    for pitchid in pitchids:
      initial = ""
      if pitchid in votes.keys():
        initial = votes[pitchid]
      logging.critical("%s %s" % (pitchid, initial,))
      self.fields[pitchid] = forms.ChoiceField(choices=PitchVote.VOTE_CHOICES, initial=initial)

  def clean(self):
    cleaned_data = self.cleaned_data
    votes = [int(v) for v in cleaned_data.values() if int(v) != 0]
    votes.sort()
    logging.critical(votes)
    if votes != [1, 2, 3, 4, 5]:
      raise forms.ValidationError("Please vote for one 1st, 2nd, 3rd, 4th and 5th choice.")
    return cleaned_data

def pitchesview(request, theclass, pitchid=None):
  theclass.menulinks = loadLinks(theclass)
  theclass.selectedmenulink = 'Pitches'
  showVideo = False
  form = None
    
  pitches = [p for p in Pitch.objects.filter(owner__in=theclass.users.filter())]

  if pitchid != None:
    pitchid = int(pitchid)
    if pitchid in [p.id for p in pitches]:
      thepitch = [p for p in pitches if p.id == pitchid][0]
      pitchindex = pitches.index(thepitch)
      nextpitch = (pitchindex + 1) % len(pitches)
      prevpitch = (pitchindex - 1) % len(pitches)
      menulinks = [MenuLink('All', reverse('course:pitches-view')),
                   MenuLink('Previous', reverse('course:pitches-view', kwargs={'pitchid' : pitches[prevpitch].id})),
                   MenuLink('Next', reverse('course:pitches-view', kwargs={'pitchid' : pitches[nextpitch].id}))]
      pitches = [thepitch]
      showVideo = True
    else:
      pitchid = None

  if not getclassuser(request, theclass):
    form = None

    if pitchid != None:
      theclass.submenulinks = initLinks(menulinks, None)
      theclass.selectedsubmenulink = None
    else:
      random.shuffle(pitches)
      theclass.submenulinks = loadPitchSubLinksAnonymous()
      theclass.selectedsubmenulink = 'View'
    
    for i,p in enumerate(pitches):
      if i % 2 == 0:
        p.style = 'even'
      else:
        p.style = 'odd'
  else:
    if theclass.classuser.role == 'Student' and len(theclass.classuser.pitches.filter(visible=True)) == 0:
      messages.warning(request, "Please complete your pitch before viewing.")
      return HttpResponseRedirect(reverse('course:pitches-edit'))

    if request.method == 'POST':
      logging.critical(request.POST)
      form = PitchVoteForm(request.POST, pitchids=[key for key in request.POST.keys() if key.startswith('pitch_')])
      pitchidPattern = re.compile(r'pitch_(\d+)')
      if form.is_valid():
        theclass.classuser.pitch_votes.clear()
        formdata = form.cleaned_data
        logging.critical(formdata)

        for field in formdata.keys():
          if formdata[field] == '0':
            continue
          else:
            pitchvote = int(formdata[field])
            pitchvoteid = int(pitchidPattern.match(field).group(1))
            logging.critical(pitchvoteid)
            newvote = PitchVote(courseuser=theclass.classuser, pitch=Pitch.objects.get(id=pitchvoteid),vote=pitchvote)
            newvote.save()
        messages.success(request, "Your votes have been saved.")
      else:
        logging.critical('Form errors.')
        logging.critical(form.errors)

    if pitchid != None and pitchid in [p.id for p in pitches]:
      pitches = [p for p in pitches if p.id == pitchid]
      theclass.submenulinks = initLinks(menulinks, None)
      theclass.selectedsubmenulink = None
      form = None
    else:
      random.shuffle(pitches)
      theclass.submenulinks = loadPitchSubLinksLoggedIn()
      theclass.selectedsubmenulink = 'Vote'
     
      otherpitches = [p for p in pitches if p.owner != theclass.classuser]
      if form == None:
        uservotes = {}
        for pitch in theclass.classuser.pitch_votes.filter():
          uservotes["pitch_%s" % (pitch.id,)] = pitch.pitchvote_set.get(courseuser=theclass.classuser).vote
          logging.critical(uservotes)
        form = PitchVoteForm(initial=uservotes, pitchids=["pitch_%s" % (str(p.id),) for p in otherpitches])
      for p in otherpitches:
        p.votingform = form['pitch_%s' % str(p.id)]

    for p in pitches:
      if theclass.classuser == p.owner:
        p.style = "owner"
        p.sort = 0
      elif theclass.classuser in p.votes.filter():
        p.style = "voter"
        p.sort = PitchVote.objects.get(courseuser=theclass.classuser, pitch=p).vote
      else:
        p.style = "other"
        p.sort = 10
    pitches.sort(key=lambda pitch: pitch.sort)

    for i,p in enumerate([p for p in pitches if p.style == "other"]):
      if i % 2 == 0:
        p.style = 'even'
      else:
        p.style = 'odd'

  return render_to_response('class/pitches/view.html',
                            {'theclass': theclass,
                             'form': form,
                             'pitches': pitches,
                             'showVideo': showVideo},
                            context_instance=RequestContext(request, current_app=theclass.app_name))

def pitchesedit(request, theclass):
  if not getclassuser(request, theclass):
    theclass.resetlinks()
    messages.warning(request, "You must log in to view this page.")
    return HttpResponseRedirect(reverse('course:login') + "?next=" + reverse('course:pitches-edit'))
  
  theclass.menulinks = loadLinks(theclass)
  theclass.selectedmenulink = 'Pitches'
  theclass.submenulinks = loadPitchSubLinksLoggedIn()
  theclass.selectedsubmenulink = 'Edit'
  fillForm = True

  if request.method == 'POST':
    form = PitchForm(request.POST)
    if form.is_valid():
      title = form.cleaned_data['title']
      description = form.cleaned_data['description']
      youtubeID = form.cleaned_data['youtubeID']
      try:
        pitch = Pitch.objects.get(owner=theclass.classuser)
        pitch.title = title
        pitch.description = description
        pitch.youtubeID = youtubeID
        pitch.visible = True
        pitch.save()
        messages.success(request, "%s: Your pitch has been updated." % (pitch.updated.strftime("%a %b %d %H:%M:%S %Y")))
      except:
        pitch = Pitch(title=title, description=description, youtubeID=youtubeID, owner=theclass.classuser, visible=True)
        pitch.save()
        messages.success(request, "%s: Your pitch has been created." % (pitch.updated.strftime("%a %b %d %H:%M:%S %Y")))
    else:
      pitch = None
  else: 
    try:
      pitch = Pitch.objects.get(owner=theclass.classuser)
      form = PitchForm({'title' : pitch.title, 'description' : pitch.description, 'youtubeID' : pitch.youtubeID })
      messages.success(request, "Loading pitch updated %s." % (pitch.updated.strftime("%a %b %d %H:%M:%S %Y")))
    except:
      pitch = None
      form = PitchForm()

  return render_to_response('class/pitches/edit.html',
                            {'theclass': theclass,
                             'form': form,
                             'pitch': pitch,},
                            context_instance=RequestContext(request, current_app=theclass.app_name))

def loadPitchSubLinksAnonymous(visible=None):
  menulinks = [MenuLink('View', reverse('course:pitches-view'))]
  return initLinks(menulinks, visible)

def loadPitchSubLinksLoggedIn(visible=None):
  menulinks = [MenuLink('Vote', reverse('course:pitches-view')),
               MenuLink('Edit', reverse('course:pitches-edit'))]
  return initLinks(menulinks, visible)

def loadProjectSubLinks(visible=None):
  menulinks = [MenuLink('Selected', reverse('course:projects-selected')),
               MenuLink('All', reverse('course:projects-all'))]
  return initLinks(menulinks, visible)

def projectsviewselected(request, theclass):
  selectedpitches = [p for p in Pitch.objects.filter(owner__in=theclass.users.filter(), selected=True)]
  random.shuffle(selectedpitches)
  theclass.submenulinks = loadProjectSubLinks()
  theclass.selectedsubmenulink = 'Selected'
  return doprojectsview(request, theclass, selectedpitches)

def projectsviewall(request, theclass):
  selectedpitches = [p for p in Pitch.objects.filter(owner__in=theclass.users.filter(), selected=True)]
  random.shuffle(selectedpitches)
  rejectedpitches = [p for p in Pitch.objects.filter(owner__in=theclass.users.filter()).exclude(selected=True)]
  logging.critical(len(rejectedpitches))
  random.shuffle(rejectedpitches)
  allpitches = selectedpitches + rejectedpitches
  theclass.submenulinks = loadProjectSubLinks()
  theclass.selectedsubmenulink = 'All'
  logging.critical(len(allpitches))
  return doprojectsview(request, theclass, allpitches)

def doprojectsview(request, theclass, pitches):
  theclass.menulinks = loadLinks(theclass)
  theclass.selectedmenulink = 'Projects'
  return render_to_response('class/pitches/viewprojects.html',
                            {'theclass': theclass,
                             'pitches': pitches,},
                            context_instance=RequestContext(request, current_app=theclass.app_name))
  
