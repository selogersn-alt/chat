with open('d:/HDIGITAL/ANDROID_ANTIGRAVITY/CHAT LOGERSN/chat/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

print("Contains toggle_blacklist:", "toggle_blacklist" in content)
print("Contains is_blacklisted:", "is_blacklisted" in content)
print("Contains sync_messages:", "def sync_messages" in content)

import re
matches = re.finditer(r'def sync_messages.*?return JsonResponse', content, re.DOTALL)
for match in matches:
    print("Found sync_messages block")
