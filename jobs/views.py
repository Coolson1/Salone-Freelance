from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .models import Job, Application, Profile, Message


# helper to build navbar links based entirely on the view logic
# caller should always pass the resulting list into the template as
# ``navbar_links``.  no conditional logic lives in the templates themselves.
def logout_view(request):
    """Logout handler that accepts both GET and POST.

    Django's built-in LogoutView blocks GET requests (HTTP 405), which
    caused problems when we rendered the link as a normal anchor.  This
    simple view just calls ``logout()`` and redirects to home.
    """
    logout(request)
    return redirect('home')


def navbar_links_for(user):
    """Return a list of dicts describing the navigation links appropriate
    for the given user.

    For anonymous users we only show sign up & login.  Once the user is
    authenticated we inspect ``user.profile.role`` and return the correct set
    of items.  A logout link is appended automatically for logged-in users.
    """
    if not user.is_authenticated:
        return [
            {'name': 'Sign Up', 'url': reverse('choose_role')},
            {'name': 'Login', 'url': reverse('login')},
        ]

    # authenticated user; fall back to empty role if profile is missing
    try:
        role = user.profile.role
    except Profile.DoesNotExist:
        role = None

    links = []
    if role == 'client':
        # clients don't really need the freelancer-only "available jobs"
        # page, so we present a "Home" link in its place and position it
        # first.  clicking it will land on the public homepage.
        links.extend([
            {'name': 'Home', 'url': reverse('home')},
            {'name': 'Post Job', 'url': reverse('post_job')},
            {'name': 'My Jobs', 'url': reverse('my_jobs')},
            {'name': 'Messages', 'url': reverse('my_conversations')},
        ])
    elif role == 'freelancer':
        # free­lancers also get a "Home" link at the front; they can still
        # browse available jobs, but home is the natural starting point.
        links.extend([
            {'name': 'Home', 'url': reverse('home')},
            {'name': 'Available Jobs', 'url': reverse('available_jobs')},
            {'name': 'My Applications', 'url': reverse('my_applications')},
            {'name': 'Messages', 'url': reverse('my_conversations')},
        ])

    # every authenticated user gets a logout link
    links.append({'name': 'Logout', 'url': reverse('logout')})
    return links


# small wrapper around render() that automatically injects ``navbar_links``
def render_with_nav(request, template_name, context=None):
    if context is None:
        context = {}
    context.setdefault('navbar_links', navbar_links_for(request.user))
    return render(request, template_name, context)


def home(request):
    """Public home page - visible to all."""
    return render_with_nav(request, 'home.html')


def available_jobs(request):
    """Job list page - only freelancers can access."""
    # If user is not authenticated, redirect to home
    if not request.user.is_authenticated:
        return redirect('home')
    
    # Check if user has a profile and role
    try:
        profile = request.user.profile
        # Only freelancers can view available jobs
        if profile.role != 'freelancer':
            return redirect('home')
    except Profile.DoesNotExist:
        return redirect('home')
    
    # only show open jobs (exclude in-progress or completed ones)
    jobs = Job.objects.filter(status='open').order_by('-created_at')
    return render_with_nav(request, 'jobs/available_jobs.html', {'jobs': jobs})


@login_required(login_url='login')
def post_job(request):
    """Post job page - only clients can access."""
    # Check if user has a profile and role
    try:
        profile = request.user.profile
        # Only clients can post jobs
        if profile.role != 'client':
            return redirect('home')
    except Profile.DoesNotExist:
        return redirect('home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        budget = request.POST.get('budget')
        if title and description and budget:
            # try to coerce budget to integer; if it fails just store 0 so
            # the record is still created. This keeps the field type as
            # IntegerField but lets users enter any value in the form.
            try:
                budget_value = int(budget)
            except (ValueError, TypeError):
                budget_value = 0

            Job.objects.create(
                title=title,
                description=description,
                budget=budget_value,
                owner=request.user,  # assign current client as owner
            )
            return redirect('home')
    return render_with_nav(request, 'jobs/post_job.html')


@login_required(login_url='login')
def apply_job(request, job_id):
    """Apply for a job - only freelancers can access."""
    # Check if user has a profile and role
    try:
        profile = request.user.profile
        # Only freelancers can apply for jobs
        if profile.role != 'freelancer':
            return redirect('home')
    except Profile.DoesNotExist:
        return redirect('home')
    
    job = get_object_or_404(Job, pk=job_id)
    if request.method == 'POST':
        applicant_name = request.POST.get('applicant_name')
        proposal = request.POST.get('proposal')
        if applicant_name and proposal:
            Application.objects.create(
                job=job,
                applicant_name=applicant_name,
                proposal=proposal,
                applicant_user=request.user,  # save linked user
            )
            return redirect('available_jobs')
    return render_with_nav(request, 'jobs/apply_job.html', {'job': job})


def choose_role(request):
    """Role selection page for signup."""
    if request.user.is_authenticated:
        return redirect('home')
    return render_with_nav(request, 'registration/choose_role.html')


# --------- new client dashboard views ----------

@login_required(login_url='login')
def my_jobs(request):
    """Display jobs posted by the logged-in client.

    Completed jobs are hidden from this listing per the new requirement.
    """
    # only clients should access this page
    try:
        if request.user.profile.role != 'client':
            return redirect('home')
    except Profile.DoesNotExist:
        return redirect('home')

    # exclude jobs already marked completed so they disappear automatically
    # annotate each job with the number of non-rejected applications; this
    # allows the template to render a badge without building a complex
    # filter expression in the template language.
    from django.db.models import Count, Q

    jobs = (
        Job.objects
        .filter(owner=request.user)
        .exclude(status='completed')
        .annotate(
            active_app_count=Count('applications',
                filter=~Q(applications__status='rejected'))
        )
        .order_by('-created_at')
    )
    return render_with_nav(request, 'jobs/my_jobs.html', {'jobs': jobs})


@login_required(login_url='login')
def job_applications(request, job_id):
    """Show applications for a single job owned by the client.

    By default the list should not include items that have already been
    rejected – the client has no reason to see them after hitting the
    "Reject" button, and the notification badge on the job card is driven
    from the same queryset.  The view still returns the full job object for
    permission checks and template headers.
    """
    job = get_object_or_404(Job, pk=job_id)

    # ensure requester owns this job
    if job.owner != request.user:
        # unauthorized access
        return redirect('home')

    # filter out rejected applications so they disappear immediately
    applications = job.applications.exclude(status='rejected')
    return render_with_nav(request, 'jobs/job_applications.html', {
        'job': job,
        'applications': applications,
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def accept_application(request, app_id):
    """Mark an application as accepted. Only job owner may do this."""
    application = get_object_or_404(Application, pk=app_id)
    job = application.job
    if job.owner != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Not authorized to accept this application")
    application.status = 'accepted'
    application.save()
    # When accepting an application, mark job as in_progress
    job.status = 'in_progress'
    job.save()
    return redirect('job_applications', job_id=job.id)


@login_required(login_url='login')
@require_http_methods(["POST"])
def reject_application(request, app_id):
    """Mark an application as rejected.

    Once rejected the object is excluded from the client's listing (see
    :func:`job_applications`), which makes it vanish from the UI and causes
    the badge count on the job card to update automatically.
    """
    application = get_object_or_404(Application, pk=app_id)
    job = application.job
    if job.owner != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Not authorized to reject this application")
    application.status = 'rejected'
    application.save()
    return redirect('job_applications', job_id=job.id)


@login_required(login_url='login')
def my_applications(request):
    """Allow freelancers to view their own applications."""
    # ensure user is freelancer
    try:
        if request.user.profile.role != 'freelancer':
            return redirect('home')
    except Profile.DoesNotExist:
        return redirect('home')

    # only show applications for jobs that are still active (open or in
    # progress).  when a client completes a job we mark the job.status =
    # 'completed', so any application tied to such a job should disappear
    # from a freelancer’s "my applications" list.  filtering here keeps the
    # code human-readable and avoids touching historical records.
    applications = Application.objects.filter(
        applicant_user=request.user
    ).exclude(job__status='completed').select_related('job')
    return render_with_nav(request, 'jobs/my_applications.html', {'applications': applications})  # keep all statuses


@login_required(login_url='login')
def conversation(request, job_id, user_id):

    """Display and post messages between job owner and an accepted freelancer."""
    job = get_object_or_404(Job, pk=job_id)
    other = get_object_or_404(User, pk=user_id)

    # Check authorization: user must be either the job owner or an accepted applicant
    is_job_owner = request.user == job.owner
    is_accepted_applicant = Application.objects.filter(
        job=job,
        applicant_user=request.user,
        status='accepted'
    ).exists()

    if not (is_job_owner or is_accepted_applicant):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Not authorized to view this conversation")

    # retrieve messages between the two for this job
    messages = Message.objects.filter(job=job).filter(
        Q(sender=request.user, receiver=other) |
        Q(sender=other, receiver=request.user)
    ).order_by('timestamp')

    # Mark all received messages as read (messages where request.user is receiver)
    Message.objects.filter(
        job=job,
        receiver=request.user,
        sender=other,
        read=False
    ).update(read=True)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=other,
                job=job,
                content=content
            )
        return redirect('conversation', job_id=job.id, user_id=other.id)

    return render_with_nav(request, 'jobs/conversation.html', {
        'job': job,
        'other': other,
        'messages': messages,
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def clear_chat(request, job_id, user_id):
    """Clear (delete) all messages in a specific conversation.
    
    Only allows clearing if the logged-in user is part of the conversation.
    Deletes messages between request.user and the other participant for that job.
    """
    job = get_object_or_404(Job, pk=job_id)
    other = get_object_or_404(User, pk=user_id)

    # Check authorization: user must be either job owner or accepted applicant
    is_job_owner = request.user == job.owner
    is_accepted_applicant = Application.objects.filter(
        job=job,
        applicant_user=request.user,
        status='accepted'
    ).exists()

    if not (is_job_owner or is_accepted_applicant):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Not authorized to clear this chat")

    # Delete all messages in this conversation
    # Messages must be between request.user and other_user for this specific job
    Message.objects.filter(
        job=job,
        sender__in=[request.user, other],
        receiver__in=[request.user, other]
    ).delete()

    return redirect('conversation', job_id=job.id, user_id=other.id)


@login_required(login_url='login')
@require_http_methods(["POST"])
def complete_job(request, job_id):
    """Mark a job as completed. Only the job owner (client) can do this.

    After completion we redirect to the client's My Jobs page with an
    optional success message.
    """
    job = get_object_or_404(Job, pk=job_id)
    if job.owner != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Not authorized to complete this job")
    job.status = 'completed'
    job.save()
    # once the job is completed we also want to make sure any application
    # for that job vanishes from a freelancer's personal list.  the
    # `my_applications` view already filters out completed jobs, but to be
    # explicit we update application statuses here as well.  keep the
    # logic easy to read for someone looking at `complete_job` later.
    #
    # accepted application may remain (might represent the worker who did
    # the job) but all others can be marked rejected.
    job.applications.exclude(status='accepted').update(status='rejected')

    # show a simple feedback message
    from django.contrib import messages
    messages.success(request, "Job marked as completed!")
    return redirect('my_jobs')



@login_required(login_url='login')
@require_http_methods(["POST"])
def delete_application(request, app_id):
    """Freelancer may delete their own rejected application.

    Only the applicant may perform this, and only when the status is
    'rejected'.  This removes clutter from their ``my_applications`` page.
    After deletion we redirect back to the freelancer dashboard.
    """
    application = get_object_or_404(Application, pk=app_id)
    if application.applicant_user != request.user or application.status != 'rejected':
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Not allowed to delete this application")
    application.delete()
    return redirect('my_applications')


def get_unread_message_count(user):
    """Helper function to get the count of unread messages for a user."""
    if not user.is_authenticated:
        return 0
    return Message.objects.filter(receiver=user, read=False).count()


@login_required(login_url='login')
def my_conversations(request):
    """Display all conversations for the current user (client or freelancer)."""
    # Get all unique jobs/users the current user has conversations with
    # A conversation exists if there are messages between the current user and another user
    
    # Get all messages where user is sender or receiver
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-timestamp').select_related('job', 'sender', 'receiver')
    
    # Extract unique conversations (one per other_user + job combination)
    conversations = {}
    for msg in messages:
        other_user = msg.sender if msg.receiver == request.user else msg.receiver
        job_id = msg.job.id
        key = (other_user.id, job_id)
        
        if key not in conversations:
            conversations[key] = {
                'job': msg.job,
                'other_user': other_user,
                'last_message_time': msg.timestamp,
                'unread_count': Message.objects.filter(
                    job=msg.job,
                    receiver=request.user,
                    sender=other_user,
                    read=False
                ).count()
            }
    
    # Sort by most recent
    sorted_conversations = sorted(
        conversations.values(),
        key=lambda x: x['last_message_time'],
        reverse=True
    )
    
    return render_with_nav(request, 'jobs/my_conversations.html', {
        'conversations': sorted_conversations
    })


@require_http_methods(["GET", "POST"])
def signup_client(request):
    """Signup page for clients."""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password and first_name and last_name:
            # Check if email already exists
            if User.objects.filter(username=email).exists():
                return render_with_nav(request, 'registration/signup.html', {
                    'error': 'Email already registered.',
                    'role': 'client'
                })
            
            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create profile with client role
            Profile.objects.create(user=user, role='client')
            
            return redirect('home')
    
    return render_with_nav(request, 'registration/signup.html', {'role': 'client'})


@require_http_methods(["GET", "POST"])
def signup_freelancer(request):
    """Signup page for freelancers."""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password and first_name and last_name:
            # Check if email already exists
            if User.objects.filter(username=email).exists():
                return render_with_nav(request, 'registration/signup.html', {
                    'error': 'Email already registered.',
                    'role': 'freelancer'
                })
            
            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create profile with freelancer role
            Profile.objects.create(user=user, role='freelancer')
            
            return redirect('home')
    
    return render_with_nav(request, 'registration/signup.html', {'role': 'freelancer'})
