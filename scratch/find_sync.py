import sys
for i, line in enumerate(open('chat/views.py', encoding='utf-8')):
    if 'sync_messages' in line:
        print(f"{i+1}: {line.strip()}")
