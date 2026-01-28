import subprocess

def send_warning_email(user_netid, slurm_job_id, gpu_allocated, used_memory_mb, gpu_node, template_path='config/warning_mail.html'):
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        html = html.replace('$net_ID', user_netid)
        html = html.replace('$job_ID', str(slurm_job_id))
        html = html.replace('$gpu_allocated', str(gpu_allocated))
        html = html.replace('$gpu_node', str(gpu_node))
        html = html.replace('$gpu_utilized', str(int(used_memory_mb) / 1000))

        subject = 'Immediate Action Required: Inefficient GPU Resource Usage Detected on Hopper Cluster'
        recipients = [str(user_netid)+"@gmu.edu","vjones20@gmu.edu","atummapu@gmu.edu"]
        sender_mail = " ".join(recipients)
        #sender_mail = f"atummapu@gmu.edu"

        command = [
            "ssh", "-t", "hop-amd-1",
            f'printf "Subject: {subject}\\nMIME-Version: 1.0\\nX-Priority: 1 (Highest)\\nImportance: High\\nContent-Type: text/html\\n\\n{html}" | sendmail {sender_mail}'
        ]

        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return True

    except subprocess.CalledProcessError as e:
        print(f"Sendmail error: {e.stderr}")
    except Exception as e:
        print(f"Unexpected email error: {e}")

    return False

