import csv
from faker import Faker
import random

fake = Faker('pt_BR')  # Using Brazilian Portuguese for names and addresses

def generate_person():
    return {
        'id': random.randint(1000, 9999),
        'name': fake.name(),
        'email': fake.email(),
        'address': fake.address().replace('\n', ', '),
        'phone': fake.phone_number(),
        'age': random.randint(18, 80)
    }

if __name__ == "__main__":
    filename = "random_people.csv"
    num_records = 2000

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'name', 'email', 'address', 'phone', 'age']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for _ in range(num_records):
            person = generate_person()
            writer.writerow(person)

    print(f"Generated {num_records} random person records in '{filename}'")
