"""
Context processor to add unread message count to all templates.
"""
from jobs.models import Message


def unread_messages(request):
    """Add unread message count to template context."""
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(receiver=request.user, read=False).count()
    else:
        unread_count = 0
    return {'unread_message_count': unread_count}
