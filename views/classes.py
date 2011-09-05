from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.http import HttpResponse, Http404
from course.models import University, Department, Offering, Semester
from django.conf.urls.defaults import *

urlpatterns = []
urlpatterns += patterns('',
                        (r'/', 'course.views.classes.offeringObjectToSummary'))

def fullUrlToSummary(request, university_slug, department_slug, offering_number, semester_slug=None):
  university = get_object_or_404(University, slug=university_slug)
  department = get_object_or_404(Department, slug=department_slug, university=university)
  offering = get_object_or_404(Offering, number=offering_number, department=department)

  return offeringObjectToSummary(request, offering, semester_slug=semester_slug)

def offeringToClass(offering):

  university = offering.department.university
  semester = get_object_or_404(Semester, current=True, university=university)

  try:
    theclass = offering.classes.filter(semester=semester)
    assert(len(theclass) == 1)
  except AssertionError:
    return None
    raise Http404

  theclass = theclass[0]
  
  # 09 Aug 2011 : GWA : Override course attributes with class ones if
  #               necessary.

  if theclass.title != "":
    title = theclass.title
  else:
    title = theclass.course.title

  if theclass.keywords != "":
    keywords = theclass.keywords
  else:
    keywords = theclass.course.keywords

  if theclass.summary != "":
    summary = theclass.summary
  else:
    summary = theclass.course.summary

def offeringObjectToSummary(request, offering, semester_slug=None):

  university = offering.department.university
  if semester_slug != None:
    semester = get_object_or_404(Semester, slug=semester_slug, university=university)
  else:
    semester = get_object_or_404(Semester, current=True, university=university)

  try:
    theclass = offering.classes.filter(semester=semester)
    assert(len(theclass) == 1)
  except AssertionError:
    raise Http404

  theclass = theclass[0]
  
  # 09 Aug 2011 : GWA : Override course attributes with class ones if
  #               necessary.

  if theclass.title != "":
    title = theclass.title
  else:
    title = theclass.course.title

  if theclass.keywords != "":
    keywords = theclass.keywords
  else:
    keywords = theclass.course.keywords

  if theclass.summary != "":
    summary = theclass.summary
  else:
    summary = theclass.course.summary

  return render_to_response('class/summary.html', 
                           {'title': title,
                            'keywords': keywords,
                            'summary': summary,
                            'university': offering.department.university,
                            'department': offering.department,
                            'offering': offering,
                            'semester': semester,
                            'theclass': theclass},
                            context_instance=RequestContext(request))
