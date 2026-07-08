import os
import sys
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatproject.settings")

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    print("SUCCESS")
except Exception as e:
    print("FAILED TO IMPORT WSGI")
    traceback.print_exc()
