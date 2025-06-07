import csv
import random
import time
from datetime import datetime, timedelta
from faker import Faker

def generate_people_csv(filename, num_records):
    fake = Faker()
    
    # Calculate date range (assuming age range 0-120 years)
    now = datetime.now()
    max_birthdate = now
    min_birthdate = now - timedelta(days=120*365)
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['name', 'age', 'birthdate_seconds']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for _ in range(num_records):
            # Generate random birthdate
            random_days = random.randint(0, (max_birthdate - min_birthdate).days)
            birthdate = min_birthdate + timedelta(days=random_days)
            
            # Calculate age
            age = (now - birthdate).days // 365
            
            # Convert birthdate to seconds since epoch
            birthdate_seconds = int(time.mktime(birthdate.timetuple()))
            
            writer.writerow({
                'name': fake.name(),
                'age': age,
                'birthdate_seconds': birthdate_seconds
            })

if __name__ == "__main__":
    print("Generating 1 million records... This may take a few minutes.")
    generate_people_csv('million_people.csv', 1_000_000)
    print("CSV file 'million_people.csv' created successfully!")