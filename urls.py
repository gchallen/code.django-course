from django.conf.urls.defaults import patterns, include, url
from course.models import Offering
from course import settings as course_settings
from django.conf import settings as site_settings
import os,urlparse

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
        urlpatterns += patterns('',
                                (r'^%s' % (link.slug),
                                 include('course.views.classes'), {'theclass': theclass}),
                                (r'^%s/%s/' % (link.slug, theclass.semester.slug),
                                 include('course.views.classes'), {'theclass': theclass}))
      else:
        pass
        urlpatterns += patterns('',
                                r'^%s/%s/' % (link.slug, theclass.semester.slug),
                                include('course.views.classes'), {'theclass': theclass})
