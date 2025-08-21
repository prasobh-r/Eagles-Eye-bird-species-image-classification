import json

file_path = "bird_species.json"

with open(file_path, "r") as json_file:
    bird_species_data = json.load(json_file)

def bdetails(name):
   return bird_species_data[name]

