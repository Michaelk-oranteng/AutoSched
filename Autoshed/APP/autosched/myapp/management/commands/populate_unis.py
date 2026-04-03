from django.core.management.base import BaseCommand
from myapp.models import University

class Command(BaseCommand):
    help = 'Populates the database with a full list of Ghanaian Universities'

    def handle(self, *args, **kwargs):
        unis = [
            # --- PUBLIC UNIVERSITIES ---
            "University of Ghana (UG)",
            "Kwame Nkrumah University of Science and Technology (KNUST)",
            "University of Cape Coast (UCC)",
            "University of Education, Winneba (UEW)",
            "University for Development Studies (UDS)",
            "University of Mines and Technology (UMaT)",
            "University of Health and Allied Sciences (UHAS)",
            "University of Energy and Natural Resources (UENR)",
            "Ghana Institute of Management and Public Administration (GIMPA)",
            "Ghana Institute of Journalism (GIJ)",
            "Ghana Institute of Languages (GIL)",
            "Ghana Communication Technology University (GCTU)",
            "Akenten Appiah-Menka University of Skills Training and Entrepreneurial Development (AAMUSTED)",
            "Simon Diedong Dombo University of Business and Integrated Development Studies (SDD-UBIDS)",
            "University of Environment and Sustainable Development (UESD)",

            # --- PUBLIC TECHNICAL UNIVERSITIES ---
            "Accra Technical University",
            "Kumasi Technical University",
            "Koforidua Technical University",
            "Cape Coast Technical University",
            "Ho Technical University",
            "Takoradi Technical University",
            "Sunyani Technical University",
            "Tamale Technical University",
            "Bolgatanga Technical University",
            "Wa Technical University",

            # --- PRIVATE UNIVERSITIES & COLLEGES ---
            "Ashesi University",
            "Central University",
            "Valley View University",
            "Academic City University College",
            "Lancaster University Ghana",
            "Webster University Ghana",
            "Regent University College of Science and Technology",
            "Pentecost University",
            "Methodist University Ghana",
            "Presbyterian University, Ghana",
            "Wisconsin International University College",
            "BlueCrest University College",
            "All Nations University",
            "Radford University College",
            "Garden City University College",
            "Kings University College",
            "Knutsford University College",
            "Maranatha University College",
            "Zenith University College",
            "Catholic University of Ghana",
            "Christian Service University College",
            "Islamic University College, Ghana",
            "Perez University College",
            "Heritage Christian College",
            "Family Health Medical School",
            "Mountcrest University College",
        ]

        self.stdout.write(self.style.MIGRATE_LABEL("Seeding all Ghanaian universities..."))
        
        count = 0
        for name in unis:
            obj, created = University.objects.get_or_create(name=name)
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Added: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Skipped (Exists): {name}'))

        self.stdout.write(self.style.SUCCESS(f'Done! Added {count} new universities.'))