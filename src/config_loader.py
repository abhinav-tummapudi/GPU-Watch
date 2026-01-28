import json
import os

def load_criterion(file_path='config/criterion.json'):
    with open(file_path, 'r') as f:
        return json.load(f)

