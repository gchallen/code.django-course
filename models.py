import os, random, string, csv, re

from django.db import models
from django.contrib.sites.models import Site
from django.conf import settings as site_settings
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.auth.models import User
from django.template import Context, loader
from django.utils.http import int_to_base36
from django.contrib.auth.tokens import default_token_generator

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
  faculty = models.ManyToManyField('Faculty', blank=True, null=True)
  users = models.ManyToManyField('CourseUser', blank=True, null=True)
  contactemail = models.EmailField()

  def __unicode__(self):
    return "%s (%s)" % (str(self.course), str(self.semester))
  
  class Meta:
    verbose_name_plural = "classes"
 
  def resetlinks(self):
    try:
      theclass.menulinks = None
    except Exception:
      pass
    try:
      theclass.submenulinks = None
    except Exception:
      pass
    try:
      theclass.selectedmenulink = ""
    except Exception:
      pass
    try:
      theclass.selectedsubmenulink = ""
    except Exception:
      pass

  def resetpassword(self, courseuser, current_app=None):

    # 14 Sep 2011 : GWA : Should be a user affiliated with this class.

    assert courseuser in self.users.filter()

    if current_app == None:
      try:
        current_app = self.app_name
      except Exception:
        current_app = None

    # 14 Sep 2011 : GWA : Try to handle the common, single-offering case.

    if current_app == None:
      try:
        o = self.offering_set.get()
        self.theoffering = o
        self.department = o.department
        l = o.offeringlink_set.filter(site=site_settings.SITE_ID)
        if len(l) == 1:
          link = l[0]
          current_app = r"%s_%s" % (link.slug, self.semester.slug)
      except Exception:
        current_app = None
    
    from django.core.mail import send_mail

    current_site = Site.objects.get_current()
    t = loader.get_template('class/reset/email.html')
    c = {
      'email' : courseuser.user.email,
      'domain' : current_site.domain,
      'site_name' : current_site.name,
      'uid' : int_to_base36(courseuser.user.id),
      'user' : courseuser.user,
      'protocol' : 'http',
      'token' : default_token_generator.make_token(courseuser.user),
      'theclass': self,
    }
    send_mail("%s%s Website Password Reset" % (self.department.shortname, self.theoffering.number),
              t.render(Context(c, current_app=current_app)),
              self.contactemail,
              [courseuser.user.email])

  def loadUserCSV(self, csvfilename):
    USER_FIELDS = {
      'firstname': True,
      'lastname': True,
      'email': True,
      'role': True,
      'idnumber': False,
    }
    csvreader = csv.DictReader(open(csvfilename, 'rb'))
    namemappings = {}
    for field in csvreader.fieldnames:
      shortfield = re.sub(r'\s+', '', field).lower()
      if shortfield in USER_FIELDS.keys():
        namemappings[shortfield] = field

    for field in USER_FIELDS.keys():
      if USER_FIELDS[field] and field not in namemappings.keys():
        return False
    
    for row in csvreader:
      firstname = row[namemappings['firstname']]
      lastname = row[namemappings['lastname']]
      email = row[namemappings['email']]
      role = row[namemappings['role']]
      try:
        idnumber = row[namemappings['idnumber']]
      except Exception:
        idnumber = ""

      existing = self.users.filter(user__email__exact=email)
      if len(existing) == 0:
        CourseUser.create(self,
                          firstname,
                          lastname,
                          email,
                          role,
                          idnumber=idnumber)


class Meeting(models.Model):
  theclass = models.ForeignKey("Class")
  
  start = models.DateTimeField()
  end = models.DateTimeField()
  location = models.CharField(max_length=256)

  optional = models.BooleanField(default=False)
  
  summary = models.CharField(max_length=1024)
  description = models.TextField(blank=True, null=True)

  def __unicode__(self):
    return "%s : %s-%s, %s : %s" % (str(self.theclass), self.start, self.end, self.location, self.summary)

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

class Paper(models.Model):
  name = models.CharField(max_length=1024)
  description = models.TextField(blank=True, null=True)

  theclass = models.ManyToManyField('Class', blank=True, null=True)
  meeting = models.ManyToManyField('Meeting', blank=True, null=True)

  paperfile = models.FileField(upload_to=lambda x, y: genfilename("paper", x, y), blank=True, null=True)
  paperlink = models.URLField(blank=True, null=True)

  papertitle = models.CharField(max_length=1024, blank=True, null=True)
  paperauthors= models.TextField(blank=True, null=True)

  def render(self):
    if self.paperlink != "":
      link = self.paperlink
    elif self.paperfile != "":
      link = self.paperfile.url
    authors = self.paperauthors.split(",")
    if len(authors) == 0:
      name = self.name
      title = self.papertitle
    elif len(authors) == 1:
      name = "%s (%s)" % (self.name, authors[0])
      title = "%s (%s)" % (self.papertitle, self.paperauthors)
    else:
      name = "%s (%s et al.)" % (self.name, authors[0])
      title = "%s (%s)" % (self.papertitle, self.paperauthors)
    return '<a href="%s" title="%s" target="_blank">%s</a>' % (link, title, name)
 
  def __unicode__(self):
    return "%s" % (self.name)

class Slides(models.Model):
  name = models.CharField(max_length=1024)
  description = models.TextField(blank=True, null=True)

  meeting = models.ManyToManyField('Meeting', blank=True, null=True)

  slidesfile = models.FileField(upload_to=lambda x, y: genfilename("slides", x, y), blank=True, null=True)
  slideslink = models.URLField(blank=True, null=True)

  def render(self):
    if self.slideslink != "":
      link = self.slideslink
    elif self.slidesfile != "":
      link = self.slidesfile.url
    return '<a href="%s" target="_blank">%s</a>' % (link, self.name)
 
  def __unicode__(self):
    return "%s" % (self.name)

class CourseUser(models.Model):
  user = models.OneToOneField(User, unique=True)
  link = models.URLField(blank=True, null=True)
  idnumber = models.CharField(max_length=32, blank=True, null=True)

  ROLE_CHOICES = (
    ('Faculty', 'Faculty'),
    ('Staff', 'Staff'),
    ('Student', 'Student'),
  )
  role = models.CharField(max_length=16, choices=ROLE_CHOICES)

  @classmethod
  def create(cls, theclass, firstname, lastname, email, role, idnumber="", link=""):
    try:
      user = User.objects.get(email=email)
    except User.DoesNotExist:
      user = User.objects.create_user(email,
                                      email,
                                      ''.join(random.choice(string.letters + string.digits + string.punctuation) for x in range(32)))
    user.first_name = firstname
    user.last_name = lastname
    user.save()
    courseuser = CourseUser(user=user, role=role, idnumber=idnumber, link=link)
    courseuser.save()
    theclass.users.add(courseuser)
    return courseuser
 

  def __unicode__(self):
    return "%s %s <%s> (%s)" % (self.user.first_name, self.user.last_name, self.user.email, self.role)
