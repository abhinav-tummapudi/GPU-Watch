#!/bin/bash

# Activate virtual environment
source /opt/slurm/prometheus_exporters/gpu-watch/watch-env/bin/activate

# Navigate to Ansible directory
cd /opt/slurm/prometheus_exporters/gpu-watch/ansible/

# Prepare log directory
mkdir -p logs
rm -f logs/*.html

# Run Ansible playbook to check timer status
ansible-playbook -i inventory.ini health_check.yml

# Generate HTML report
html_file="logs/email_report.html"

# Start HTML structure
cat <<EOF > "$html_file"
<html><head>
<style>
  body { font-family: Arial, sans-serif; background-color: #111; color: #eee; }
  h2 { text-align: center; color: #f44336; }
  table { width: 80%; margin: auto; border-collapse: collapse; background-color: #222; }
  th, td { border: 1px solid #444; padding: 8px; text-align: left; }
  th { background-color: #333; }
  td.inactive { color: #f44336; }
</style>
</head><body>
<h2>Inactive - gpu-watch.timer</h2>
<table>
<tr><th>Hostname</th><th>Status</th></tr>
EOF

# Append rows for each host
for f in logs/*.html; do
  [[ "$(basename "$f")" == "email_report.html" ]] && continue
  host=$(basename "$f" .html)
  status=$(grep -o 'Status:.*' "$f" | awk '{print $2}')
  echo "<tr><td>$host</td><td class=\"inactive\">❌ $status</td></tr>" >> "$html_file"
done

# Close HTML
echo "</table></body></html>" >> "$html_file"

# Send email only if inactive entries are found
if grep -q "<td class=\"inactive\">" "$html_file"; then
    subject="[ALERT] GPU WATCH DOWN on Some Nodes"
    sender_mail="atummapu@gmu.edu vjones20@gmu.edu"
    html=$(<"$html_file")

    ssh -T hop-amd-1 "
      {
        printf 'Subject: %s\nMIME-Version: 1.0\nX-Priority: 1 (Highest)\nImportance: High\nContent-Type: text/html\n\n' \"$subject\"
        printf '%s\n' \"$html\"
      } | sendmail $sender_mail
    "
    echo "Email Sent"
else
    echo "✅ gpu-watch.timer is active on all nodes. No email sent."
fi
