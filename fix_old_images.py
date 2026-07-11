import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatproject.settings')
django.setup()

from chat.models import Message

def fix_old_media_urls():
    messages = Message.objects.filter(attachment_url__startswith='https://graph.facebook.com/')
    count = 0
    for msg in messages:
        url = msg.attachment_url
        # extract media_id from the end of the URL
        media_id = url.rstrip('/').split('/')[-1]
        
        # update to new format
        msg.attachment_url = f"/api/media/{media_id}/"
        msg.save()
        count += 1
        print(f"Updated message {msg.id}: {url} -> {msg.attachment_url}")
        
    print(f"Fix complete! {count} messages updated.")

if __name__ == "__main__":
    fix_old_media_urls()
