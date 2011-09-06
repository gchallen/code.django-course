from django.conf.urls.defaults import patterns, include, url
from course.models import Offering
from course import settings as course_settings
from django.conf import settings as site_settings
import os,urlparse

def loadClass(theclass, offering):

  theclass.university = offering.department.university
  theclass.department = offering.department
  theclass.theoffering = offering
  
  # 09 Aug 2011 : GWA : Override course attributes with class ones if
  #               necessary.

  if theclass.title == "":
    theclass.title = theclass.course.title

  if theclass.keywords == "":
    theclass.keywords = theclass.course.keywords

  if theclass.summary == "":
    theclass.summary = theclass.course.summary

  return theclass

urlpatterns = []

if course_settings.FullCourseURLs:
  urlpatterns +=\
      patterns('course.views',
               (r'^(?P<university_slug>\w+)/(?P<department_slug>\w+)/(?P<offering_number>\d+)/((?P<semester_slug>\w+)/)?$',
                'classes.fullUrlToSummary'))

for offering in Offering.on_site.all():
  for link in offering.offeringlink_set.filter(site=site_settings.SITE_ID):
    for theclass in offering.classes.all():
      if theclass.semester.current == True:
        base = r'%s' % (link.slug)
        urlpatterns += patterns('',
                                (base,
                                 include('course.views.classes'),
                                 {'theclass': loadClass(theclass, offering)}))
      base = r'%s/%s' % (link.slug, theclass.semester.slug)
      urlpatterns += patterns('',
                              (base,
                               include('course.views.classes'),
                               {'theclass': loadClass(theclass, offering)}))
