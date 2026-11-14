
import json
import urllib.request
import urllib.error

url = "http://127.0.0.1:5000/add_student"

student = {
    "admission_no": "TMU011",
    "name": "Test Student",
    "email": "teststudent@gmail.com",
    "phone": "9876500011",
    "gender": "Male",
    "date_of_birth": "2006-05-15",
    "admission_date": "2026-11-05",
    "department_id": 1,
    "current_semester": 1,
    "status": "Active"
}

data = json.dumps(student).encode("utf-8")

request = urllib.request.Request(
    url,
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(request) as response:
        print("Status:", response.status)
        print("Response:", response.read().decode())

except urllib.error.HTTPError as error:
    print("Error:", error.code)
    print(error.read().decode())

except urllib.error.URLError as error:
    print("Connection Error:", error.reason)
