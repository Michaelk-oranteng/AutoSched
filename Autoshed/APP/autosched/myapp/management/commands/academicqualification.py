from django.core.management.base import BaseCommand
from myapp.models import AcademicLevel, MainProgram

class Command(BaseCommand):
    help = 'Populates the database with Academic Levels and Main Programs'

    def handle(self, *args, **kwargs):
        # 1. Define Academic Levels
        levels = [
            {'name': 'Diploma', 'code': 'DIP', 'category': 'Undergraduate'},
            {'name': 'Higher National Diploma', 'code': 'HND', 'category': 'Undergraduate'},
            {'name': 'Bachelor Degree', 'code': 'DEG', 'category': 'Undergraduate'},
            {'name': 'Master of Science', 'code': 'MSc', 'category': 'Postgraduate'},
            {'name': 'Doctor of Philosophy', 'code': 'PhD', 'category': 'Postgraduate'},
            {'name': 'Other Qualifications', 'code': 'OTH', 'category': 'Other'},
        ]

        # 2. Define standard Main Programs
        main_programs = [
            'Computer Science', 'Information Technology', 'Software Engineering',
            'Business Administration', 'Accounting', 'Mechanical Engineering',
            'Electrical Engineering', 'Civil Engineering', 'Nursing', 'Pharmacy'
        ]

        self.stdout.write(self.style.MIGRATE_LABEL("Seeding Academic Qualifications..."))
        
        # Seed Levels
        for item in levels:
            obj, created = AcademicLevel.objects.update_or_create(
                code=item['code'], 
                defaults=item
            )
            status = "Added" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f'{status} Level: {item["name"]}'))

        self.stdout.write(self.style.MIGRATE_LABEL("\nSeeding Main Programs..."))

        # Seed Main Programs
        for name in main_programs:
            obj, created = MainProgram.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Added Program: {name}'))

        self.stdout.write(self.style.SUCCESS('\nDatabase seeding completed successfully!'))