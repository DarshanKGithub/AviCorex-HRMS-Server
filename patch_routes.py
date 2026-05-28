import re

with open('app/api/routes/leave.py', 'r') as f:
    content = f.read()

# Replace all occurrences of employee_id in LeaveRequestPublic dict mapping with employee_id and employee_name
content = re.sub(
    r"'employee_id': (lr|r|updated)\.employee_id,",
    r"'employee_id': \1.employee_id,\n            'employee_name': getattr(\1.employee, 'full_name', None) if getattr(\1, 'employee', None) else None,",
    content
)

with open('app/api/routes/leave.py', 'w') as f:
    f.write(content)

