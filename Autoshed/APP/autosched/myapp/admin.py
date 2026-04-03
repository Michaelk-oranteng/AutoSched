from django.contrib import admin
from .models import UserProfile, University, Course, Program, Room, Lecturer, Department


# Register your models here.
admin.site.register(Course)
admin.site.register(Department)
admin.site.register(Lecturer)
admin.site.register(Program)
admin.site.register(Room)
admin.site.register(UserProfile)
admin.site.register(University)





