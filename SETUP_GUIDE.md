## Django Freelance Marketplace - Role-Based Authentication Setup

This guide walks you through running the refactored marketplace with role-based authentication.

### What Changed

1. **Authentication System Added**
   - Profile model to store user roles (Client or Freelancer)
   - Signup flow with role selection
   - Django LoginView for login/join
   - Logout functionality

2. **Page Structure Reorganized**
   - Home page (/) - Public, no login required
   - Available Jobs (/available-jobs/) - Freelancers only
   - Post Job (/post/) - Clients only
   - Role-based access control with redirects

3. **URL Configuration Updated**
   - / → home page (new)
   - /signup/ → choose role
   - /signup/client/ → client registration
   - /signup/freelancer/ → freelancer registration
   - /join/ → login page
   - /logout/ → logout
   - /available-jobs/ → job listings (moved from /)
   - /post/ → post job (unchanged)
   - /apply/<job_id>/ → apply for job (unchanged)

4. **New Templates Added**
   - templates/home.html
   - templates/registration/choose_role.html
   - templates/registration/signup.html
   - templates/registration/login.html
   - templates/jobs/available_jobs.html

5. **Updated Templates**
   - base.html - improved navbar with login/signup links

6. **Models Updated**
   - New Profile model with OneToOneField to User
   - Job and Application models unchanged

---

### Step-by-Step Setup Instructions

#### 1. Navigate to Project Directory

```powershell
cd "c:\DESKTOP_STUFFS\All Code\fiver\marketplace"
```

#### 2. Activate Virtual Environment (if using one)

```powershell
.\venv\Scripts\Activate.ps1
```

#### 3. Create New Migrations

Since the Profile model was added, create migrations:

```powershell
python manage.py makemigrations
```

Expected output:

```
Migrations for 'jobs':
  jobs/migrations/0001_initial.py
    - Create model Job
    - Create model Profile
    - Create model Application
```

#### 4. Apply Migrations

```powershell
python manage.py migrate
```

Expected output:

```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, jobs
Running migrations:
  Applying jobs.0001_initial... OK
  (and other Django migrations...)
```

#### 5. Create Superuser (Optional, for Admin Access)

```powershell
python manage.py createsuperuser
```

Follow prompts to create admin account.

#### 6. Run Development Server

```powershell
python manage.py runserver
```

Server running at: http://127.0.0.1:8000/

---

### Testing the Application

#### Public Home Page

- Go to: http://127.0.0.1:8000/
- See: Welcome page with signup options
- No login required

#### Sign Up as Client

1. Click "Sign Up" in navbar
2. Choose "Sign Up as Client"
3. Fill form (First Name, Last Name, Email, Password)
4. Submit
5. Redirected to home
6. Log in with email/password
7. Access: /post/ to post jobs
8. Blocked: /available-jobs/ redirects to home

#### Sign Up as Freelancer

1. Click "Sign Up" in navbar
2. Choose "Sign Up as Freelancer"
3. Fill form (First Name, Last Name, Email, Password)
4. Submit
5. Redirected to home
6. Log in with email/password
7. Access: /available-jobs/ to browse jobs
8. Blocked: /post/ redirects to home

#### Test Login/Logout

1. Logged-in users see "Logout" in navbar
2. Click "Logout" → redirects to home
3. Click "Join" → login page
4. Enter registered email and password

#### Admin Interface

- Go to: http://127.0.0.1:8000/admin/
- Login with superuser account
- Manage Profiles, Jobs, Applications

---

### Code Files Summary

**models.py:**

- Profile: OneToOneField to User, role choices (client/freelancer)
- Job: title, description, budget, created_at
- Application: job FK, applicant_name, proposal, created_at

**views.py:**

- home(): Public home page
- available_jobs(): Freelancer-only job listing
- post_job(): Client-only job posting (login required)
- apply_job(): Freelancer-only application (login required)
- choose_role(): Role selection page
- signup_client(): Client registration
- signup_freelancer(): Freelancer registration

**urls.py (Project):**

- Includes auth views (LoginView, LogoutView)
- Routes all signup, login, logout URLs
- Includes jobs app URLs

**urls.py (Jobs App):**

- /available-jobs/
- /post/
- /apply/<int:job_id>/

**Templates:**

- base.html: Responsive navbar with auth links
- home.html: Public welcome page
- registration/choose_role.html: Role selection
- registration/signup.html: Registration form
- registration/login.html: Login form
- jobs/available_jobs.html: Job listings
- jobs/post_job.html: Unchanged
- jobs/apply_job.html: Unchanged

**settings.py additions:**

- LOGIN_REDIRECT_URL = 'home'
- LOGOUT_REDIRECT_URL = 'home'

**CSS Updates:**

- Flexbox navbar with left/right sections
- Home page hero section
- Card-based layouts for auth pages and job listings
- Better form styling and focus states
- Error message styling

---

### Role-Based Access Control

**Clients:**

- ✅ Access: Homepage, Post Job page, Auth pages, Logout
- ❌ Blocked: Available Jobs page (redirects to home)

**Freelancers:**

- ✅ Access: Homepage, Available Jobs page, Apply page, Auth pages, Logout
- ❌ Blocked: Post Job page (redirects to home)

**Not Authenticated:**

- ✅ Access: Public homepage, Signup, Login
- ❌ Blocked: Post Job page (login_required), Apply page (login_required)
- Accessing /available-jobs/ redirects to home (not a protected page, but role-limited)

---

### Important Notes

1. **Static Files Setup:**
   - CSS is at: `static/jobs/css/styles.css`
   - JavaScript is at: `static/jobs/js/scripts.js`
   - Both loaded in base.html with {% static %} tag

2. **Email as Username:**
   - Users register with email
   - Users login with email as username

3. **No Auto-Login:**
   - After signup, users are redirected to home
   - They must click "Join" and login manually

4. **Role is Immutable:**
   - Users cannot change roles after signup
   - To change role, create new account

5. **Database:**
   - SQLite database (db.sqlite3) created automatically
   - Delete if you want to reset and start fresh

---

### Troubleshooting

**TemplateSyntaxError with 'static' tag:**

- Ensure `{% load static %}` is at top of base.html ✅ Already done

**Profile matching query does not exist:**

- Run migrations: `python manage.py migrate`
- Recreate user accounts after migration

**NoReverseMatch URL:**

- Ensure all URL names match in views and templates
- Check urls.py for typos

**Cannot apply for job / post job:**

- User must be logged in
- User must have correct role (freelancer to apply, client to post)

---

### Next Steps for Expansion

If you want to add features later:

1. **Messaging System:**
   - Add Message model
   - Create message views and templates
   - Update navbar with message link

2. **User Profiles/Portfolio:**
   - Extend Profile model
   - Add freelancer portfolio page

3. **Job Filtering:**
   - Add category, difficulty fields to Job
   - Filter by category, price range

4. **Payment Integration:**
   - Integrate Stripe or similar
   - Create payment model

5. **Search & Pagination:**
   - Add search form to available jobs
   - Paginate job listings

---

**Project is Now Ready!** 🚀

All code is clean, beginner-friendly, and easy to modify.
