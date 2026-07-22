with open('d:/HDIGITAL/ANDROID_ANTIGRAVITY/CHAT LOGERSN/chat/views.py', 'rb') as f:
    content = f.read()

print("is_blacklisted count:", content.count(b'is_blacklisted'))
print("toggle_blacklist count:", content.count(b'toggle_blacklist'))

# Search around line 580
lines = content.decode('utf-8').splitlines()
for i in range(575, 590):
    print(f"{i+1}: {lines[i]}")
