import subprocess
import pandas as pd
import re

def get_nvidia_processes():
    try:
        output = subprocess.run([
            "nvidia-smi",
            "--query-compute-apps=gpu_uuid,pid,used_memory,process_name",
            "--format=csv,noheader,nounits"
        ], stdout=subprocess.PIPE, text=True, check=True)

        lines = [line.replace(',', '').strip().split() for line in output.stdout.split('\n') if line.strip()]
        df = pd.DataFrame(lines, columns=['GPU_UUID', 'PID', 'USED_MEMORY', 'PROCESS_NAME'])
        df['USED_MEMORY'] = pd.to_numeric(df['USED_MEMORY'], errors='coerce')
        return df
    except subprocess.CalledProcessError:
        return pd.DataFrame()

def map_pid_to_job(pid):
    try:
        cgroup = subprocess.run(["cat", f"/proc/{pid}/cgroup"], stdout=subprocess.PIPE, text=True, check=True).stdout
        match = re.search(r'job_(\d+)', cgroup)
        
        if match:
            array_ID = subprocess.run(
                ["sacct", "-Xj", str(match.group(1)), "--format=JobID", "--noheader"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            ).stdout
            if '_' in array_ID:
                return array_ID.split('_')[0]
            return array_ID.split('\n')[0].replace(" ","")
            # return match.group(1)
        return None

        #if match:
            #return match.group(1)

    except Exception:
        return None

