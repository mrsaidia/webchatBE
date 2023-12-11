import subprocess

# Ví dụ: Chạy lệnh 'ls' để liệt kê các file và thư mục
command = "python3.10 test.py"

# Chạy lệnh và thu thập đầu ra
result = subprocess.run(
    [command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
)

# In đầu ra chuẩn (stdout)
print("Đầu ra chuẩn (stdout):")
print(result.stdout)

# In lỗi, nếu có (stderr)
if result.stderr:
    print("Đầu ra lỗi (stderr):")
    print(result.stderr)
