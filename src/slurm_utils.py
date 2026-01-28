import subprocess
import pandas as pd

def get_hostname():
    result = subprocess.run(['hostname'], stdout=subprocess.PIPE, text=True, check=True)
    return result.stdout.strip().split('.')[0]

def get_running_jobs(node):
    try:
        output = subprocess.run(['squeue', '-w', node, '--state=R'], stdout=subprocess.PIPE, text=True, check=True)
        lines = output.stdout.strip().split('\n')
        data = [line.split() for line in lines]
        return pd.DataFrame(data[1:], columns=data[0])
    except subprocess.CalledProcessError:
        return pd.DataFrame()

