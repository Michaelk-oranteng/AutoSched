from django.db import models
from django.contrib.auth.models import User
import random as rnd
import math
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save, post_delete
from datetime import timedelta, date


# 1. The University Table
class University(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)    
    contact = models.CharField(max_length=10)
    institution = models.ForeignKey(University, on_delete=models.SET_NULL, null=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    
    @property
    def initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        return "?"
    
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class AcademicLevel(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    category = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class MainProgram(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Program(models.Model):
    academic_level = models.ForeignKey(AcademicLevel, on_delete=models.CASCADE)
    main_program = models.ForeignKey(MainProgram, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        if self.specialization:
            return f"{self.main_program.name} - {self.specialization}"
        return self.main_program.name
    
class Department(models.Model):
    dept_name = models.CharField(max_length=255)
    dept_code = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.dept_name} ({self.dept_code})"
    
class Specialization(models.Model):
    name = models.CharField(max_length=255)
    main_program = models.ForeignKey(MainProgram, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.main_program.name} ({self.name})"
    
class Course(models.Model):
    COURSE_TYPE_CHOICES = [
        ('CORE', 'Core Subject'),
        ('SPEC', 'Specialization Subject'),
    ]
    course_name = models.CharField(max_length=255)
    course_code = models.CharField(max_length=255)
    course_type = models.CharField(max_length=10, choices=COURSE_TYPE_CHOICES, default='CORE')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    level = models.ForeignKey(AcademicLevel, on_delete=models.CASCADE)
    semester = models.PositiveIntegerField(default=1) 
    
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, blank=True)    
    program = models.ManyToManyField(Program, related_name='courses', blank=True)
    credit_hours = models.PositiveIntegerField(default=3) 
    expected_students = models.PositiveIntegerField(default=30) 
        
    def __str__(self):
        return f"{self.course_code}: {self.course_name}"
    
class Room(models.Model):
    room_name = models.CharField(max_length=255)
    room_capacity = models.PositiveIntegerField() 
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
        
    def __str__(self):
        return f"{self.room_name} ({self.room_capacity} seats)"
    
class Lecturer(models.Model):
    lec_fname = models.CharField(max_length=255)
    lec_lname = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    # CHANGE: Many-to-Many Relationship
    # This allows a Lecturer to teach multiple Courses
    courses = models.ManyToManyField(Course, related_name='lecturers')
    
    lec_email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    lec_contact = models.CharField(max_length=10)
    
    def __str__(self):
        return f"{self.lec_fname} {self.lec_lname}"
    
    
class TimetableSlot(models.Model):
    # CHANGE: ForeignKey instead of OneToOne
    # If a course meets twice a week, you need multiple slots for one course.
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    assigned_day = models.CharField(max_length=20)
    assigned_time = models.CharField(max_length=50)
    
    # CHANGE: Link to the Room object directly rather than a string
    assigned_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    
    semester = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.course.course_code} | {self.assigned_day} | {self.assigned_time}"
    
    
