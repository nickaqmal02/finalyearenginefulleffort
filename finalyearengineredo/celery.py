"""Celery app — wires Django settings into the task queue.

Run the worker in a separate terminal:
    celery -A finalyearengineredo worker -l info
Run the beat scheduler (for periodic tasks):
    celery -A finalyearengineredo beat -l info
"""

import os

from celery import Celery

# Tell Celery to use Django's settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finalyearengineredo.settings')

app = Celery('finalyearengineredo')

# Pull CELERY_* settings from Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in every installed app (looks for tasks.py)
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """A simple test task — call from shell to verify Celery works."""
    print(f'Request: {self.request!r}')
