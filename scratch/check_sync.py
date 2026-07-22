import re
with open('d:/HDIGITAL/ANDROID_ANTIGRAVITY/CHAT LOGERSN/chat/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'def sync_messages' in line:
        print(f"sync_messages found at line {i+1}")
        break

for i, line in enumerate(lines):
    if 'is_blacklisted' in line:
        print(f"is_blacklisted found at line {i+1}")
