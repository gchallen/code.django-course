from django.db import models
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager
import os.path, random, string

# 05 Aug 2011 : GWA : TODO (Long term) : Move to photologue.

# 03 Aug 2011 : GWA : TODO : Validation for all model types. Clean up and comment.

# 03 Aug 2011 : GWA : A course is an ongoing occurrence of a particular set of
#               materials being taught.

class Course(models.Model):

  # 03 Aug 2011 : GWA : Title and keywords can be added to or overwritten by
  #               the class instance.

  title = models.CharField(max_length=256)
  keywords = models.CharField(max_length=1024, blank=True, null=True)
  summary = models.TextField(blank=True, null=True)
  
  # 03 Aug 2011 : GWA : Should probably point to a list of links to each class
  #               taught as part of this course.

  link = models.URLField()

  def __unicode__(self):
    return self.title

# 03 Aug 2011 : GWA : A class is an instance of a course.

class Class(models.Model):
  course = models.ForeignKey("Course")

  # 03 Aug 2011 : GWA : Subsumes course-wide information.

  title = models.CharField(max_length=256, blank=True, null=True)
  title.help_text = "Use this to override the course title."

  keywords = models.CharField(max_length=1024, blank=True, null=True)
  keywords.help_text = "Use this to override the course keywords."

  summary = models.TextField(blank=True, null=True)
  summary.help_text = "Use this to override the course summary."
  
  # 03 Aug 2011 : GWA : Supplants course-wide information.

  classtitle = models.CharField(max_length=256, blank=True, null=True)
  classtitle.verbose_name = "Additional class title"
  classtitle.help_text = "Use this to add to the course title."

  classkeywords = models.CharField(max_length=1024, blank=True, null=True)
  classkeywords.verbose_name = "Additional class keywords"
  classkeywords.help_text = "Use this to add to the course keywords."

  classsummary = models.TextField(blank=True, null=True)
  classsummary.verbose_name = "Additional class summary"
  classsummary.help_text = "Use this to add to the course summary."
 
  # 03 Aug 2011 : GWA : Specific to a given class.

  semester = models.ForeignKey('Semester')
  overview = models.TextField(blank=True, null=True)
  faculty = models.ManyToManyField('Faculty')

  def __unicode__(self):
    return "%s (%s)" % (str(self.course), str(self.semester))
  
  class Meta:
    verbose_name_plural = "classes"

class Meeting(models.Model):
  theclass = models.ForeignKey("Class")
  
  start = models.DateTimeField()
  end = models.DateTimeField()
  location = models.CharField(max_length=256)

  optional = models.BooleanField(default=False)
  
  summary = models.CharField(max_length=1024)
  description = models.TextField(blank=True, null=True)

# 15 Aug 2011 : GWA : Offering links decouple the offering from the naming and
#               allow mirroring. For example, users could have both:
#               
#               http://phonelab.cse.buffalo.edu/course AND
#               http://blue.cse.buffalo.edu/courses/cse622
#
#               Point to the same place. In this case we would set up one
#               server (blue.cse, e.g.) as the root to host the database and
#               serve static content, while the mirror (phonelab.cse) simply
#               installs a django-course instance and sets up the database
#               accessor and STATIC_URL field properly.

class OfferingLink(models.Model):
  site = models.ForeignKey(Site)
  offering = models.ForeignKey('Offering')
  slug = models.SlugField(blank=True)
  objects = models.Manager()
  on_site = CurrentSiteManager()

  def __unicode__(self):
    return "http://%s/<django.courses prefix>/%s -> %s" %\
        (str(self.site),
         self.slug,
         str(self.offering))

class Offering(models.Model):
  
  # 03 Aug 2011 : A set of University/Department/Number's uniquely identifies a
  #               course. Callers can choose how collapse these if they desire:
  #               i.e., # Buffalo, CSE, 452 and Buffalo, CSE, 552 could be
  #               rendered Buffalo CSE 452/552.
  
  department = models.ForeignKey('Department')
  classes = models.ManyToManyField("Class")
  number = models.IntegerField()
  sites = models.ManyToManyField(Site, through='OfferingLink')
  objects = models.Manager()
  on_site = CurrentSiteManager()
  
  def __unicode__(self):
    return "%s %s %d" % (self.department.university.shortname,
                         self.department.shortname,
                         self.number)

class University(models.Model):
  fullname = models.CharField(max_length=256)
  fullname.verbose_name = "Full Name"
  fullname.help_text = "Example: The University at Buffalo, The State University of New York"

  name = models.CharField(max_length=256)
  name.verbose_name = "Name"
  name.help_text = "Example: SUNY Buffalo"

  shortname = models.CharField(max_length=32)
  shortname.verbose_name = "Short Name"
  shortname.help_text = "Example: UB"
 
  slug = models.SlugField(unique=True)
  slug.verbose_name = "Name Slug"
  slug.help_text = "Example: UB, U_Toronto"

  link = models.URLField(blank=True, null=True)
  logo = models.ImageField(upload_to=lambda x, y: genfilename("university", x, y), blank=True, null=True)
  class Meta:
    verbose_name_plural = "universities"
  
  def __unicode__(self):
    return self.name

class Department(models.Model):
  university = models.ForeignKey("University")
  fullname = models.CharField(max_length=256)
  fullname.verbose_name = "Full Name"
  fullname.help_text = "Example: Department of Computer Science and Engineering"

  name = models.CharField(max_length=256)
  name.verbose_name = "Name"
  name.help_text = "Example: Computer Science and Engineering"

  shortname = models.CharField(max_length=32)
  shortname.verbose_name = "Short Name"
  shortname.help_text = "Example: CSE"
  
  slug = models.SlugField()
  slug.verbose_name = "Name Slug"
  slug.help_text = "Example: CSE, Folk_and_Myth"

  link = models.URLField(blank=True, null=True)
  logo = models.ImageField(upload_to=lambda x, y: genfilename("department", x, y), blank=True, null=True)
  
  def __unicode__(self):
    return "%s %s" % (str(self.university), self.name)

class Semester(models.Model):
  university = models.ForeignKey('University')
  
  name = models.CharField(max_length=32, unique=True)
  name.help_text = "Example: Fall 2011. Used for printing."

  slug = models.SlugField(max_length=32, unique=True)
  slug.help_text = "Example: Fall2011."

  start = models.DateField()
  start.verbose_name = "Semester Start (Inclusive)"
  
  end = models.DateField()
  end.verbose_name = "Semester End (Inclusive)"

  classesstart = models.DateField()
  classesstart.verbose_name = "Classes Start (Inclusive)"

  classesend = models.DateField()
  classesend.verbose_name = "Classes End (Inclusive)"
  
  readingstart = models.DateField()
  readingstart.verbose_name = "Reading Period Starts (Inclusive)"

  readingend = models.DateField()
  readingend.verbose_name = "Reading Period Ends (Inclusive)"
  
  examsstart = models.DateField()
  examsstart.verbose_name = "Exams Start (Inclusive)"

  examsend = models.DateField()
  examsend.verbose_name = "Exams End (Inclusive)"
  
  current = models.BooleanField(default=False)
  
  def __unicode__(self):
    return "%s" % (self.name)

class Holiday(models.Model):
  university = models.ForeignKey('University')
  label = models.CharField(max_length=128)
  start = models.DateTimeField()
  end = models.DateTimeField()

class Faculty(models.Model):
  departments = models.ManyToManyField('Department')
  name = models.CharField(max_length=128)
  photo = models.ImageField(upload_to=lambda x, y: genfilename("faculty", x, y), blank=True, null=True)
  link = models.URLField(blank=True, null=True)
  email = models.EmailField()
  username = models.CharField(max_length=32, blank=True, null=True)
  
  def __unicode__(self):
    return "%s (%s)" % (self.name, self.email)
  
  class Meta:
    verbose_name_plural = "faculty members"

class Contribution(models.Model):
  summary = models.CharField(max_length=256)
  supporter = models.ForeignKey('Supporter')
  description = models.TextField()
  toclass = models.ForeignKey('Class', blank=True, null=True)

  def __unicode__(self):
    return "%s to %s (%s)" % (self.supporter.name, self.toclass.course.title, self.toclass.semester.name)

class Supporter(models.Model):
  name = models.CharField(max_length=128)
  link = models.URLField(blank=True, null=True)
  logo = models.ImageField(upload_to=lambda x, y: genfilename("supporter", x, y), blank=True, null=True)
  logoprimarycolor = models.CharField(max_length=6, blank=True, null=True)
  def __unicode__(self):
    return self.name

def genfilename(key, instance, filename):
  return "django-course/%s/%s%s" % \
      (key,
       ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32)),
       os.path.splitext(filename)[1])
