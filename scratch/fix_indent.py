import sys

def fix_indent(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Lines 327 to 368 (0-indexed 326 to 367)
    for i in range(326, 368):
        lines[i] = "    " + lines[i]

    # Lines 378 to 528 (0-indexed 377 to 527)
    for i in range(377, 528):
        if lines[i].strip(): # Only indent if not empty
            lines[i] = "    " + lines[i]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

if __name__ == "__main__":
    fix_indent("d:/HDIGITAL/ANDROID_ANTIGRAVITY/CHAT LOGERSN/chat/views.py")
