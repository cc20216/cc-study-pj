import os
import subprocess

os.chdir(r'c:\Users\general-c\OneDrive\桌面\dbstudy')
git_path = r'C:\Users\general-c\AppData\Local\GitHubDesktop\app-3.5.4\resources\app\git\cmd\git.exe'

subprocess.run([git_path, 'config', '--local', 'user.name', 'CC20216'])
subprocess.run([git_path, 'config', '--local', 'user.email', '2821680845@qq.com'])
result = subprocess.run([git_path, 'config', '--local', '--list'], capture_output=True, text=True)
print(result.stdout)