"""
WSGI config for gaming_leaderboard project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaming_leaderboard.settings')

application = get_wsgi_application()
