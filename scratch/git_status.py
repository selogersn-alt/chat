import subprocess
result = subprocess.run(['git', 'status'], capture_output=True, text=True, cwd='d:/HDIGITAL/ANDROID_ANTIGRAVITY/CHAT LOGERSN')
print(result.stdout)
