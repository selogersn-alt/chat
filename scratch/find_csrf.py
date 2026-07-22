with open('d:/HDIGITAL/ANDROID_ANTIGRAVITY/CHAT LOGERSN/chat/templates/chat/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'csrftoken' in line:
        print(f"Line {i+1}: {line.strip()}")
