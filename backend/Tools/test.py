# print("Hello World")
from file_permissions import check_file_permissions

result = check_file_permissions.invoke({"file_path": "demo.py"})
print(result)
