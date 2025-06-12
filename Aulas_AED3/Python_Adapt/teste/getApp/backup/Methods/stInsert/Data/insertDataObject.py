import csv

data_objects = []
with open('traffic_accidents_rev2 (1).csv', 'r') as f:
    reader = csv.reader(f, delimiter=';')
    next(reader)  # Skip header row
    for row in reader:
        data_objects.append(DataObject(row))