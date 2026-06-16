import os
import subprocess

os.chdir(r'c:\Users\general-c\OneDrive\桌面\dbstudy')
git_path = r'C:\Users\general-c\AppData\Local\GitHubDesktop\app-3.5.4\resources\app\git\cmd\git.exe'

print("=== 添加文件 ===")
result = subprocess.run([git_path, 'add', '.'], capture_output=True, text=True)
print("stdout:", result.stdout)
print("stderr:", result.stderr)

print("\n=== 检查状态 ===")
result = subprocess.run([git_path, 'status'], capture_output=True, text=True)
print(result.stdout)

print("\n=== 提交 ===")
result = subprocess.run([git_path, 'commit', '-m', 'chore: initial commit - Django学习管理系统'], capture_output=True, text=True)
print("stdout:", result.stdout)
print("stderr:", result.stderr)