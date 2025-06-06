import csv
import random

def generate_fruit_data(num_registries, filename="fruits_data.csv"):
    """Generates a CSV file with fruit species data."""
    fruits = [
        "Apple", "Banana", "Orange", "Mango", "Strawberry", "Blueberry",
        "Raspberry", "Pineapple", "Watermelon", "Grape", "Kiwi", "Peach",
        "Pear", "Plum", "Cherry", "Lemon", "Lime", "Avocado", "Coconut",
        "Pomegranate", "Fig", "Date", "Grapefruit", "Guava", "Papaya"
    ]
    regions = [
        "Tropical", "Subtropical", "Temperate", "Mediterranean", "Arid"
    ]
    colors = [
        "Red", "Yellow", "Orange", "Green", "Purple", "Blue", "Pink", "Brown"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["SpeciesName", "Region", "Color", "IsEdible", "TypicalWeight_g"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for i in range(num_registries):
            writer.writerow({
                "SpeciesName": f"{random.choice(fruits)} {random.choice(['var.', 'subsp.'])} {random.randint(1, 100)}",
                "Region": random.choice(regions),
                "Color": random.choice(colors),
                "IsEdible": random.choice([True, False]),
                "TypicalWeight_g": round(random.uniform(10, 1000), 2)
            })
    print(f"Generated '{filename}' with {num_registries} records.")

if __name__ == "__main__":
    num_registries = 210000
    generate_fruit_data(num_registries)
