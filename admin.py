from course.models import Course, Class, Offering, University, Department,\
    Semester, Holiday, Faculty, Supporter, Contribution, OfferingLink,\
    Meeting, Paper, Slides, CourseUser, Pitch
from django.contrib.sites.models import Site
from django.contrib import admin

admin.site.register(Course)
admin.site.register(Class)
admin.site.register(Offering)
admin.site.register(University)
admin.site.register(Department)
admin.site.register(Semester)
admin.site.register(Holiday)
admin.site.register(Faculty)
admin.site.register(Supporter)
admin.site.register(Contribution)
admin.site.register(OfferingLink)
admin.site.register(Meeting)
admin.site.register(Paper)
admin.site.register(Slides)
admin.site.register(CourseUser)
admin.site.register(Pitch)
