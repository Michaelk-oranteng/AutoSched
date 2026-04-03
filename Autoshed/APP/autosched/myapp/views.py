from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password, ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils.http import urlencode
from datetime import datetime
from .models import UserProfile
from django.db.models import Q
from django.contrib.auth import update_session_auth_hash
import csv
import io
import pandas as pd
from django.db import transaction

from .models import (
    UserProfile, AcademicLevel, Program, Department, 
    Course, Room, Lecturer, TimetableSlot, MainProgram
)
from .forms import SignupForm, ResetForm, LoginForm
from .Engine import GeneticAlgorithm



# --- Helper functions ---

def format_date_for_display(date_str):
    """Converts 'YYYY-MM-DD' into 'Jan. 01, 2026'."""
    if not date_str or date_str in ['', 'None', 'CURRENT', 'SESSION', 'undefined']:
        return None
    if isinstance(date_str, datetime):
        return date_str.strftime('%b. %d, %Y')
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%b. %d, %Y')
    except (ValueError, TypeError):
        return None

# --- Basic Authentication Views ---

def home(request):
    return render(request, 'myapp/index.html')

def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email_input = form.cleaned_data['email']
        password_input = form.cleaned_data['password']
        user = UserProfile.objects.filter(email__iexact=email_input).first()
        if user and check_password(password_input, user.password):
            request.session['user_id'] = user.id
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('dashboard')
        messages.error(request, "Invalid email or password.")
    return render(request, "myapp/login.html", {"form": form})

def signup_view(request):
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].lower()
        if UserProfile.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, "myapp/signup.html", {"form": form})
        
        password = form.cleaned_data["password"]
        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return render(request, "myapp/signup.html", {"form": form})

        UserProfile.objects.create(
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            email=email,
            contact=form.cleaned_data.get("contact", ""),
            institution=form.cleaned_data.get("institution"),
            password=make_password(password)
        )
        messages.success(request, "Account created successfully.")
        return redirect("login_view")
    return render(request, "myapp/signup.html", {"form": form})

# --- Password Reset ---

def reset_view(request):
    form = ResetForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email_to_check = form.cleaned_data['email']
        if UserProfile.objects.filter(email__iexact=email_to_check).exists():
            return redirect('reset_confirm', email=email_to_check)
        messages.error(request, "No account found with that email address.")
    return render(request, "myapp/reset.html", {"form": form})

def reset_confirm(request, email):
    if request.method == "POST":
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if not new_password or new_password != confirm_password:
            messages.error(request, "Passwords must match and cannot be empty.")
            return render(request, "myapp/reset_confirm.html", {"email": email})
        
        if len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return render(request, "myapp/reset_confirm.html", {"email": email})

        user = UserProfile.objects.filter(email__iexact=email).first()
        if user:
            user.password = make_password(new_password)
            user.save()
            messages.success(request, "Password updated successfully!")
            return redirect('login_view')
        return redirect('reset')
    return render(request, "myapp/reset_confirm.html", {"email": email})



def dashboard(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login_view')
    
    user = UserProfile.objects.select_related('institution').get(id=user_id)

    if request.method == "POST":
        # 1. Department Logic
        if 'add_department' in request.POST:
            Department.objects.create(
                dept_name=request.POST.get('dept_name'),
                dept_code=request.POST.get('dept_code')
            )
            messages.success(request, "Department added successfully.")

        # 2. Program Logic
        elif 'add_program' in request.POST:
            al_id = request.POST.get('academic_level_id')
            mp_id = request.POST.get('main_program_id')
            spec = request.POST.get('specialization')
            if al_id and mp_id:
                Program.objects.create(
                    academic_level_id=al_id,
                    main_program_id=mp_id,
                    specialization=spec
                )
                messages.success(request, "Academic Program added.")

        # 3. Course Logic (Updated for Many-to-Many)
        elif 'add_course' in request.POST:
            lvl_id = request.POST.get('level_id')
            dept_id = request.POST.get('department_id')
            c_type = request.POST.get('course_type')
            prog_ids = request.POST.getlist('program_id') 

            # 1. Create the course instance first (without M2M field)
            new_course = Course.objects.create(
                course_name=request.POST.get('course_name'),
                course_code=request.POST.get('course_code'),
                course_type=c_type,
                department_id=dept_id,
                level_id=lvl_id,
                semester=int(request.POST.get('semester') or 1),
                expected_students=int(request.POST.get('expected_students') or 30),
                credit_hours=int(request.POST.get('credit_hours') or 3)
            )
            
            # 2. Add the Many-to-Many relationships
            if prog_ids:
                new_course.program.add(*prog_ids)
            messages.success(request, "Course created and linked to programs.")

        # 4. Room Logic
        elif 'add_room' in request.POST:
            Room.objects.create(
                room_name=request.POST.get('room_name'),
                room_capacity=int(request.POST.get('room_capacity')),
                department_id=request.POST.get('department_id')
            )
            messages.success(request, "Room added.")

        # 5. Lecturer Logic
        elif 'add_lecturer' in request.POST:
            email = request.POST.get('lec_email')
            
            lec, created = Lecturer.objects.update_or_create(
                lec_email__iexact=email,
                defaults={
                    'lec_fname': request.POST.get('lec_fname'),
                    'lec_lname': request.POST.get('lec_lname'),
                    'lec_contact': request.POST.get('lec_contact'),
                    'department_id': request.POST.get('department_id'),
                    'lec_email': email 
                }
            )
            
            course_ids = request.POST.getlist('lec_courses')
            if course_ids:
                # Use set() to overwrite or add() to append depending on your preference
                lec.courses.set(course_ids) 
            
            if created:
                messages.success(request, f"Lecturer {lec.lec_fname} registered.")
            else:
                messages.info(request, f"Updated profile for {lec.lec_fname}.")
                
        return redirect('dashboard')

    # Updated Context with optimized queries
    context = {
        'user': user,
        'levels': AcademicLevel.objects.all(),
        'main_programs': MainProgram.objects.all(),
        'departments': Department.objects.all(),
        'programs': Program.objects.all().select_related('main_program', 'academic_level'),
        # Change: use prefetch_related for Many-to-Many fields
        'courses': Course.objects.all().select_related('level', 'department').prefetch_related('program'),
        'rooms': Room.objects.all().select_related('department'),
        'lecturers': Lecturer.objects.all().prefetch_related('courses', 'department'),
    }
    return render(request, "myapp/dashboard.html", context)

def upload_data_view(request):
    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        messages.error(request, "No file uploaded.")
        return redirect("dashboard")

    file_name = uploaded_file.name.lower()

    # Validate file type
    if not file_name.endswith((".csv", ".xlsx", ".xls")):
        messages.error(request, "Only CSV or Excel files are allowed.")
        return redirect("dashboard")

    try:
        # Read file
        if file_name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Basic validation
        if df.empty:
            messages.error(request, "Uploaded file is empty.")
            return redirect("dashboard")

        # 🔧 Example: iterate rows (customize per model)
        for _, row in df.iterrows():
            print(row.to_dict())  # Replace with actual save logic

        messages.success(request, "Data uploaded successfully.")

    except Exception as e:
        messages.error(request, f"Upload failed: {str(e)}")

    return redirect("dashboard")

def download_template(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bulk_upload_template.csv"'

    writer = csv.writer(response)
    
    # These are the headers you requested
    writer.writerow([
        'Academic Level', 
        'Main Program', 
        'Specialization', 
        'Department Name', 
        'Short Code', 
        'Course Name', 
        'Course Code', 
        'Course Category',
        'Link to Program',
        'Department',
        'Semester',
        'Student Count',
        'Credit Hours',
        'Room Name',
        'Seating Capacity',
        'Department',
        'First Name',
        'Last Name',
        'Assigned Courses',
        'Department',
        'Email',
        'Contact'        
    ])
    
    # Add a sample row to guide the user (Optional)
    writer.writerow([
        'Undergraduate', 
        'Computer Science', 
        'Data Science', 
        'School of IT', 
        'SIT', 
        'Database Systems', 
        'CS302', 
        'leave blank if core subject',
        'Program name',
        'department name',
        'First or Second',
        'Student Count',
        'Credit Hours',
        'Room name',
        'Stundent Count',
        'Department associated to' ,       
        'lecturers First name',
        'lecturers last name',
        'Assigned courses',
        'Department under',
        'Email of lecturer',
        'Contact of lecturer'
    ])

    return response

# --- Timetable Generation Logic ---

def generate(request):
    user_id = request.session.get('user_id')
    if not user_id: 
        return redirect('login_view')

    current_user = UserProfile.objects.select_related('institution').filter(id=user_id).first()

    # 1. Capture Filters
    start_date = request.GET.get('start', '')
    end_date = request.GET.get('end', '')
    selected_level_id = request.GET.get('level')
    selected_mp_id = request.GET.get('program')
    selected_spec = request.GET.get('specialization') 
    
    selected_level_obj = AcademicLevel.objects.filter(id=selected_level_id).first()
    selected_mp_obj = MainProgram.objects.filter(id=selected_mp_id).first()
    
    current_program_obj = None
    timetable_slots = []

    if selected_level_obj and selected_mp_obj:
        # 2. Logic: Identify ALL related programs for this Level + Main Program
        # This includes the Core (no spec) and EVERY specialization under it
        all_related_programs = Program.objects.filter(
            academic_level=selected_level_obj,
            main_program=selected_mp_obj
        ).distinct()

        # We pick one "Primary" program object just for the header display
        if selected_spec:
            current_program_obj = all_related_programs.filter(specialization=selected_spec).first()
        else:
            current_program_obj = all_related_programs.first()
            
        courses = Course.objects.filter(
            program__academic_level=selected_level_obj,
            program__main_program=selected_mp_obj
        ).prefetch_related(
            'lecturers', 'program'
        ).distinct()



        # 4. Check for existing Slots or show TBD
        slots = TimetableSlot.objects.filter(course__in=courses).select_related('course', 'assigned_room')

        if slots.exists():
            for s in slots:
                timetable_slots.append({
                    'program': s.course.program.first(),
                    'semester': s.semester,
                    'course_code': s.course.course_code,
                    'course_name': s.course.course_name,
                    'assigned_day': s.assigned_day,
                    'assigned_time': s.assigned_time,
                    'assigned_venue': s.assigned_room.room_name if s.assigned_room else "TBA",
                    'lecturers': s.course.lecturers.all(),
                })
        else:
            for c in courses:
                timetable_slots.append({
                    'program': s.course.program.first(),
                    'semester': c.semester,
                    'course_code': c.course_code,
                    'course_name': c.course_name,
                    'lecturers': c.lecturers.all(),
                })

    context = {
        'user': current_user,
        'levels': AcademicLevel.objects.all(),
        'available_programs': MainProgram.objects.all(),
        'specializations': Program.objects.filter(main_program=selected_mp_obj).values_list('specialization', flat=True).distinct() if selected_mp_obj else [],
        'selected_level': selected_level_id,
        'selected_program': selected_mp_id,
        'selected_spec': selected_spec,
        'start_date': start_date,
        'end_date': end_date,
        'formatted_start_date': format_date_for_display(start_date),
        'formatted_end_date': format_date_for_display(end_date),
        'current_program_obj': current_program_obj,
        'timetable_slots': timetable_slots,
    }
    return render(request, "myapp/generate.html", context)

def delete_item(request, item_type, item_id):
    if request.method == "POST":
        models_map = {
            'course': Course,
            'room': Room,
            'lecturer': Lecturer,
            'department': Department,
            'program': Program
        }
        
        model = models_map.get(item_type)
        if model:
            obj = model.objects.filter(id=item_id).first()
            if obj:
                obj.delete()
                messages.success(request, f"{item_type.capitalize()} deleted successfully.")
    
    return redirect('dashboard')

def run_timetable_engine(request):
    """
    Triggers the Genetic Algorithm to generate a timetable while ensuring 
    zero conflicts with lecturers or rooms already booked by other programs.
    """
    if request.method != "POST": 
        return redirect('generate')
    
    # 1. Capture POST Data
    mp_id = request.POST.get('program_name') 
    lvl_id = request.POST.get('level_id')
    spec = request.POST.get('specialization')
    start_date = request.POST.get('start_date', '')  
    end_date = request.POST.get('end_date', '')      

    try:
        # 2. Identify the Courses for the current target (Core + Selected Specialization)
        # We use Q objects to handle the "Core or Specialization" logic
        course_query = Q(program__main_program_id=mp_id, program__academic_level_id=lvl_id)
        
        # Prefetch lecturers to speed up the Genetic Algorithm's conflict checking
        courses = Course.objects.filter(course_query).prefetch_related('lecturers', 'program').distinct()
        rooms = list(Room.objects.all())

        if not courses.exists():
            messages.error(request, "No courses found to schedule for this selection.")
            return redirect('generate')

        # --- THE CROSS-DEPARTMENT CONFLICT FIX ---
        # 3. Fetch all slots ALREADY in the database that belong to OTHER programs.
        # This prevents an Undergrad class from taking a room/lecturer already used by a Masters class.
        existing_slots = TimetableSlot.objects.exclude(course__in=courses).select_related(
            'course', 'assigned_room'
        ).prefetch_related('course__lecturers')

        # 4. Initialize the Genetic Engine
        # We pass existing_slots as a 'constraint' list the engine must respect
        ga = GeneticAlgorithm(
            courses=list(courses), 
            rooms=rooms, 
            existing_slots=list(existing_slots) 
        )
        
        # 5. Run Evolution
        # generations/pop_size balanced for web-server timeout limits
        best_schedule = ga.evolve(generations=200, population_size=100)

        # 6. Atomic Database Update
        if best_schedule:
            with transaction.atomic():
                # Step A: Remove only the old slots for THIS specific group of courses
                TimetableSlot.objects.filter(course__in=courses).delete()
                
                # Step B: Insert the new optimized slots
                for item in best_schedule:
                    start_h = item['start_time']
                    end_h = start_h + item['duration']
                    # Standardizing the time format for the grid view
                    time_str = f"{start_h:02d}:00 - {end_h:02d}:00"

                    TimetableSlot.objects.create(
                        course=item['course_obj'],
                        assigned_day=item['day'],
                        assigned_time=time_str,
                        assigned_room=item['room'],
                        semester=item['course_obj'].semester
                    )
            
            messages.success(request, f"Timetable successfully evolved! Resource conflicts with other programs were resolved.")
            
            # 7. Construct Redirect URL with all filters intact for the Grid View
            query_params = urlencode({
                'program': mp_id,
                'level_id': lvl_id,
                'start': start_date,
                'end': end_date
            })

            return redirect(f"{reverse('timetable_grid')}?{query_params}")
        else:
            messages.error(request, "The engine could not find a conflict-free solution. Try increasing room availability.")

    except Exception as e:
        # Log the full error to the console for the developer
        import traceback
        print(traceback.format_exc()) 
        messages.error(request, f"Engine Error: {str(e)}")
    
    return redirect('generate')

def timetable_grid_view(request):
    # 1. Get IDs, Specialization, and Dates from the URL parameters
    lvl_id = request.GET.get('level_id')
    mp_id = request.GET.get('program')
    spec_name = request.GET.get('spec')  # Capture the specialization name
    raw_start = request.GET.get('start')
    raw_end = request.GET.get('end')
    
    # 2. Fetch the Objects
    level_obj = AcademicLevel.objects.filter(id=lvl_id).first()
    main_prog_obj = MainProgram.objects.filter(id=mp_id).first()
    
    # Find a primary mapping for the header (prioritize the one with the spec)
    program_mapping = Program.objects.filter(
        academic_level=level_obj, 
        main_program=main_prog_obj,
        specialization=spec_name if spec_name else None
    ).first()

    # 3. Get University Name from the logged-in user
    user_id = request.session.get('user_id')
    user = UserProfile.objects.select_related('institution').filter(id=user_id).first()
    institution_name = user.institution.name if user and user.institution else "TIMETABLE SYSTEM"

    # 4. Fetch the generated slots using "Core + Spec" logic
    # We want courses that belong to this Main Program and Level
    course_filter = Q(
        course__program__main_program=main_prog_obj,
        course__program__academic_level=level_obj
    )

    if spec_name and spec_name != 'None' and spec_name != '':
        # Filter: Only show Core (isnull) OR the specific specialization
        course_filter &= (
            Q(course__program__specialization__isnull=True) | 
            Q(course__program__specialization=spec_name)
        )
    # If no spec_name is provided, it will naturally show everything for that Program/Level
    # which matches your "populate all" requirement.

    slots = TimetableSlot.objects.filter(course_filter).select_related(
        'course', 
        'assigned_room', 
        'course__level'
    ).prefetch_related(
        'course__program', 
        'course__lecturers'
    ).distinct().order_by('assigned_day', 'assigned_time')

    # 5. Build Context
    context = {
        'slots': slots,
        'institution': institution_name,
        'program': program_mapping,
        'selected_spec': spec_name,
        'level_name': level_obj.name if level_obj else "Unknown Level",
        'program_name_fallback': main_prog_obj.name if main_prog_obj else "Program",
        'start_date': format_date_for_display(raw_start),
        'end_date': format_date_for_display(raw_end),
    }
    
    return render(request, 'myapp/timetable_grid.html', context)




def upload_data_view(request):
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        messages.error(request, "No file uploaded.")
        return redirect("dashboard")

    def safe_int(value, default=1):
        try:
            if pd.isna(value) or str(value).strip().lower() in ["", "nan", "none"]: return default
            return int(float(''.join(filter(lambda x: x.isdigit() or x == '.', str(value)))))
        except:
            return default

    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = [c.strip() for c in df.columns]

        with transaction.atomic():
            for _, row in df.iterrows():
                # 1. ACADEMIC LEVEL
                level_name = str(row.get('Academic Level', 'Undergraduate')).strip()
                level_obj, _ = AcademicLevel.objects.get_or_create(name=level_name)

                # 2. DEPARTMENT
                dept_name = str(row.get('Department Name', '')).strip()
                dept_obj = None
                if dept_name and dept_name.lower() != "nan":
                    dept_code = str(row.get('Short Code', '')).strip()
                    dept_obj, _ = Department.objects.get_or_create(
                        dept_name=dept_name, 
                        defaults={'dept_code': dept_code if dept_code.lower() != "nan" else dept_name[:3].upper()}
                    )

                # 3. MAIN PROGRAM & SPECIFIC PROGRAM
                mp_name = str(row.get('Main Program', '')).strip()
                prog_obj = None
                if mp_name and mp_name.lower() != "nan":
                    main_p, _ = MainProgram.objects.get_or_create(name=mp_name)
                    spec_name = str(row.get('Specialization', '')).strip()
                    
                    # Links MainProgram + Level + Specialization
                    prog_obj, _ = Program.objects.get_or_create(
                        main_program=main_p,
                        academic_level=level_obj,
                        specialization=None if not spec_name or spec_name.lower() == "nan" else spec_name
                    )

                # 4. COURSE & LINK TO PROGRAM
                course_code = str(row.get('Course Code', '')).strip()
                course_obj = None
                if course_code and course_code.lower() != "nan":
                    course_obj, _ = Course.objects.update_or_create(
                        course_code=course_code,
                        defaults={
                            'course_name': row.get('Course Name', course_code),
                            'course_type': row.get('Course Category', 'CORE'),
                            'level': level_obj,
                            'department': dept_obj,
                            'semester': safe_int(row.get('Semester'), 1),
                            'expected_students': safe_int(row.get('Student Count'), 30),
                            'credit_hours': safe_int(row.get('Credit Hours'), 3)
                        }
                    )
                    # Add the program to the course's Many-to-Many field
                    if prog_obj:
                        course_obj.program.add(prog_obj)

                # 5. LECTURER & LINK TO COURSE
                lec_email = str(row.get('Email', '')).strip()
                if lec_email and lec_email.lower() != "nan":
                    lecturer, _ = Lecturer.objects.update_or_create(
                        lec_email__iexact=lec_email,
                        defaults={
                            'lec_fname': row.get('First Name', 'TBA'),
                            'lec_lname': row.get('Last Name', ''),
                            'lec_contact': row.get('Contact', ''),
                            'department': dept_obj
                        }
                    )
                    # Add the course to the lecturer's Many-to-Many field
                    if course_obj:
                        lecturer.courses.add(course_obj)

                # 6. ROOMS
                room_name = str(row.get('Room Name', '')).strip()
                if room_name and room_name.lower() != "nan":
                    Room.objects.update_or_create(
                        room_name=room_name,
                        defaults={
                            'room_capacity': safe_int(row.get('Seating Capacity'), 40),
                            'department': dept_obj
                        }
                    )

        messages.success(request, "Timetable data successfully imported!")
    except Exception as e:
        messages.error(request, f"Error processing file: {str(e)}")

    return redirect("dashboard")

login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        messages.success(request, 'Profile updated successfully!')
    return redirect('dashboard')

@login_required
def update_contact(request):
    if request.method == 'POST':
        # Assuming you have a Profile model linked to User
        profile = request.user.profile 
        profile.phone = request.POST.get('phone')
        profile.save()
        messages.success(request, 'Contact details updated!')
    return redirect('dashboard')

@login_required
def change_password(request):
    if request.method == 'POST':
        new_pass = request.POST.get('new_password')
        user = request.user
        user.set_password(new_pass)
        user.save()
        # This keeps the user logged in after the password change
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed successfully!')
    return redirect('dashboard')
