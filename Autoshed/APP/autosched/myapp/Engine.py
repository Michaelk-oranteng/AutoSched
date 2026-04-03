import random
import copy

class GeneticAlgorithm:
    def __init__(self, courses, rooms, existing_slots=None):
        self.courses = courses  
        self.rooms = rooms      
        # existing_slots are TimetableSlot objects from other programs already in the DB
        self.existing_slots = existing_slots if existing_slots else []
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.possible_start_hours = [8, 9, 10, 11, 12, 13, 14, 15, 16]

    def is_overlapping(self, gene_a, gene_b):
        """Checks overlap between two genes within the current population."""
        if gene_a['day'] != gene_b['day']:
            return False
        return gene_a['start_time'] < (gene_b['start_time'] + gene_b['duration']) and \
               (gene_a['start_time'] + gene_a['duration']) > gene_b['start_time']

    def is_overlapping_with_db(self, gene, existing_slot):
        """Checks overlap between a gene and a TimetableSlot object from the database."""
        if gene['day'] != existing_slot.assigned_day:
            return False
        
        # Parse existing "08:00 - 11:00" string from database
        try:
            times = existing_slot.assigned_time.split(' - ')
            ex_start = int(times[0].split(':')[0])
            ex_end = int(times[1].split(':')[0])
            
            gene_start = gene['start_time']
            gene_end = gene['start_time'] + gene['duration']
            
            # Logic: (StartA < EndB) and (EndA > StartB)
            return gene_start < ex_end and gene_end > ex_start
        except (ValueError, IndexError):
            return False

    def create_individual(self):
        individual = []
        for course in self.courses:
            valid_rooms = [r for r in self.rooms if r.department_id == course.department_id]
            course_lecturers = list(course.lecturers.all())
            
            gene = {
                "course_obj": course,
                "lecturers": course_lecturers,
                "room": random.choice(valid_rooms) if valid_rooms else random.choice(self.rooms),
                "day": random.choice(self.days),
                "start_time": random.choice(self.possible_start_hours),
                "duration": course.credit_hours, 
                "program_ids": list(course.program.values_list('id', flat=True)),
                "level_id": course.level.id
            }
            individual.append(gene)
        return individual

    def calculate_fitness(self, individual):
        penalties = 0
        
        for i, gene_a in enumerate(individual):
            # --- 1. Basic Hard Constraints ---
            if gene_a['room'] and gene_a['course_obj'].expected_students > gene_a['room'].room_capacity:
                penalties += 100 

            if (gene_a['start_time'] + gene_a['duration']) > 18:
                penalties += 150

            # --- 2. Global Conflict Check (Against other programs in DB) ---
            for existing in self.existing_slots:
                if self.is_overlapping_with_db(gene_a, existing):
                    # Room Conflict with another department/program
                    if gene_a['room'] == existing.assigned_room:
                        penalties += 500  # High penalty to prevent double-booking rooms
                    
                    # Lecturer Conflict with another department/program
                    existing_lecs = list(existing.course.lecturers.all())
                    if any(lec in existing_lecs for lec in gene_a['lecturers']):
                        penalties += 500

            # --- 3. Internal Conflict Check (Within current schedule) ---
            for j in range(i + 1, len(individual)):
                gene_b = individual[j]
                
                if self.is_overlapping(gene_a, gene_b):
                    if gene_a['room'] == gene_b['room']:
                        penalties += 200
                    
                    common_lecs = set(gene_a['lecturers']) & set(gene_b['lecturers'])
                    if common_lecs:
                        penalties += 200
                    
                    shared_progs = set(gene_a['program_ids']) & set(gene_b['program_ids'])
                    if shared_progs and gene_a['level_id'] == gene_b['level_id']:
                        penalties += 300

        return -penalties

    def crossover(self, parent_a, parent_b):
        point = random.randint(0, len(parent_a) - 1)
        return parent_a[:point] + parent_b[point:]

    def mutate(self, individual, mutation_rate=0.1):
        new_individual = copy.deepcopy(individual) 
        for gene in new_individual:
            if random.random() < mutation_rate:
                choice = random.choice(['day', 'time', 'room'])
                if choice == 'day':
                    gene['day'] = random.choice(self.days)
                elif choice == 'time':
                    gene['start_time'] = random.choice(self.possible_start_hours)
                elif choice == 'room':
                    dept_rooms = [r for r in self.rooms if r.department_id == gene['course_obj'].department_id]
                    gene['room'] = random.choice(dept_rooms) if dept_rooms else random.choice(self.rooms)
        return new_individual

    def evolve(self, population_size=50, generations=500):
        population = [self.create_individual() for _ in range(population_size)]
        
        for gen in range(generations):
            population.sort(key=lambda ind: self.calculate_fitness(ind), reverse=True)
            
            if self.calculate_fitness(population[0]) == 0:
                return population[0]

            new_population = population[:2] # Elitism

            while len(new_population) < population_size:
                parent_a = random.choice(population[:10])
                parent_b = random.choice(population[:10])
                
                child = self.crossover(parent_a, parent_b)
                child = self.mutate(child)
                new_population.append(child)
            
            population = new_population
            
        return population[0]