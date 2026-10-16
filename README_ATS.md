# Tawreed Job Portal & Recruitment Workspace

This package adds a working recruitment application to the approved Tawreed website. The corporate pages retain their original copy, hero, service carousels, assets and scripts. Their only change is a Job Portal link before the existing header contact button, plus its equivalent in the mobile menu. The existing Employee Portal / ERP preview is separate and unchanged.

## Start locally

1. Extract the complete ZIP into a writable folder. Install Python **3.10 or newer** from [python.org](https://www.python.org/downloads/) if it is not already installed.
2. On macOS, open **Start Job Portal.command**. On Windows, open **Start Job Portal.cmd**. On Linux, run `python3 backend/start_portal.py` from the extracted folder. The launcher installs the pinned Python dependencies on its first run, so internet access is needed for that first setup.
3. At the first launch, enter your administrator name, email and a unique password of 12–128 characters in the terminal. Password input is hidden. The public portal opens at `http://127.0.0.1:8765/jobs.html`. Open `http://127.0.0.1:8765/recruiter-login.html` for the management dashboard. Keep the launcher window open; Ctrl+C stops the service.

No default administrator, real credential, published vacancy, candidate, database or CV is shipped. If macOS does not preserve the launcher's executable flag after extraction, run `python3 backend/start_portal.py` in the extracted directory. If port 8765 is in use, stop your earlier local preview or set `ATS_PORT` to a free port before starting. The launcher never stops another process.

The corporate website can still be previewed by opening index.html directly. Job search, applications and recruitment management require the application server; a static file preview cannot provide authentication or save applications. The new portal displays a clear connection message in that situation. All ATS styling, fonts, logos and scripts are local. The original marketing pages retain their existing optional external photography and Tailwind CDN behaviour.

## Candidate journey

- Open **Job Portal** in the global header. Search by title/keyword and filter by expertise, emirate and employment type. Results are paginated in groups of 12.
- Open **View role & apply** to see the full description, responsibilities, requirements, benefits, location, salary range when published, closing date and unique reference.
- Complete contact details, current location, UAE visa/residency status, notice period and relevant experience. Salary and visa-expiry fields are optional. Upload a PDF or DOCX CV up to 8 MB and consent to processing for this vacancy.
- A successful submission displays a unique `TWD-APP-…` reference. Duplicate applications using the same email for the same vacancy are rejected. Closing a vacancy or passing its closing date stops further submissions.
- Receipt is displayed on-screen. Email/SMS notifications are not configured or sent. There is no candidate account or promise of live application-status tracking.

## Administrator and recruiter workflows

### Accounts

Administrators use **Team access → Create account** to assign recruiter or administrator access with a temporary password. Share the password using an approved secure channel. The recipient must change it at first sign-in before using the dashboard. Administrators can disable/re-enable accounts, change roles and reset passwords. Changes revoke existing sessions. The last active administrator cannot be disabled or downgraded. Users change their own password under **My account**; that change also invalidates other sessions.

Recruiters can see and manage only vacancies assigned to them and applications for those vacancies. Administrators can review all vacancies, candidates, team accounts and activity records. Assignment is controlled by administrators in the vacancy editor. A recruiter cannot reassign a job or access another recruiter's CV by changing a URL.

### Vacancy approval

1. **Create vacancy** and complete the title, expertise, emirate, location, employment type, closing date, summary, role description, responsibilities and requirements. Add salary and benefits when appropriate. Administrators can assign an active recruiter.
2. **Save draft** keeps the vacancy private. **Submit for approval** moves it into the pending queue.
3. An administrator selects **Approve & publish** or **Return**, recording an amendment note when returning it. Only approved, published and unexpired vacancies appear publicly.
4. **Edit** saves a fresh draft and removes any previous publication approval. The job must be submitted and approved again. The editor states this before saving. Closing a vacancy immediately removes it from public results while retaining its applications.
5. A closed vacancy may be resubmitted for approval after its information and closing date are checked. Concurrent edits are guarded by a version number; stale saves are rejected rather than silently overwriting another person's changes.

### Applicant tracking

Open **Applications**, filter by vacancy or stage, or search by candidate name, email or application reference. **Open profile** shows the submitted information, CV download, consent record, private notes and stage history. Allowed stage choices are enforced by the API:

| Current stage | Allowed next stages |
|---|---|
| Applied | Screening, Rejected, Withdrawn |
| Screening | Shortlisted, Rejected, Withdrawn |
| Shortlisted | Interview, Rejected, Withdrawn |
| Interview | Offer, Shortlisted, Rejected, Withdrawn |
| Offer | Hired, Interview, Rejected, Withdrawn |
| Hired / Rejected / Withdrawn | Terminal; history remains available |

Decisions remain human actions; the system does not automatically rank, reject or select candidates based on visa, nationality, salary or other attributes. Private notes and stage decisions record the acting user and time. CV downloads are authenticated, restricted to the assigned recruiter or an administrator, sent as attachments and logged. The administrator can permanently delete an application and its CV, notes and stage history after a confirmation in the interface. The audit retains the deletion event and opaque reference, not the deleted candidate profile.

## Directory and persistence

```text
Tawreed - Web Package/
  index.html … existing corporate pages (header insertion only)
  jobs.html                      Public job search
  job-details.html               Role detail and application form
  recruiter-login.html           Recruitment sign-in
  recruiter.html                 Administrator / recruiter dashboard
  css/ats.css                    Isolated new components
  js/ats-common.js                Same-origin API and safe DOM helpers
  js/ats-public.js                Search, job detail and application flow
  js/ats-admin.js                 Authenticated management interface
  backend/
    app.py                       API, permissions, storage and static allowlist
    manage.py                    Administrator creation, password recovery, backup, local serving
    start_portal.py               Cross-platform setup and launch
    wsgi.py                      Production application entry point
    requirements.txt             Pinned dependencies
    tests/test_ats.py             Automated integration tests
    package_release.py           Safe release packaging
  Start Job Portal.command       macOS launcher
  Start Job Portal.cmd           Windows launcher
  README_ATS.md                  This guide
```

By default, data is saved in a sibling directory named `tawreed-ats-data`, outside the website folder. SQLite contains users, hashed passwords, hashed session tokens, vacancies, candidate records, stage history and audit entries. CVs are saved under random filenames in its private `resumes` directory, not inside public assets. The local virtual environment is also a sibling directory, `.tawreed-ats-runtime`. Keep these directories when replacing website code. Do not place them under a web server document root or include them in a distributable ZIP.

Set `ATS_DATA_DIR` to an absolute private persistent path for a different location. POSIX directories are created with mode 0700 and database/CV files with mode 0600; use equivalent restrictive service-account ACLs on Windows. Disk encryption and encrypted backups are infrastructure responsibilities and are not supplied by SQLite itself.

## Security controls implemented

- Argon2id password hashing; no plain-text password storage or password recovery by email.
- Opaque server-side sessions. Only a hash of each token is retained. HttpOnly, SameSite=Strict cookies; Secure cookies in production. Idle expiry 30 minutes, maximum session lifetime 8 hours. Login rotates sessions; logout, account changes and password changes revoke them.
- CSRF tokens on every write endpoint, same-origin Origin checks, no permissive CORS policy, parameterised SQL, role checks and per-record ownership checks.
- Login, anonymous-session and application rate limits. Input lengths, enum values, date and amount ranges are checked server-side. Public response fields exclude recruiter identity and review notes.
- PDF/DOCX extension, size and structural checks; DOCX macros, embedded objects and unsafe external relationships rejected. PDFs with obvious scripts/embedded media rejected. Original filenames are sanitised. Uploaded contents are never inserted into HTML or served from public assets.
- A mandatory ClamAV scan in production, failing closed when unavailable or infected. Local mode reports that antivirus is not configured; structural validation alone is not a malware guarantee.
- The four ATS pages use a self-only JavaScript Content Security Policy. Candidate and vacancy text is rendered through DOM text nodes, without evaluating submitted HTML. API and workspace responses disable caching. Sensitive files are not accessible through the static server allowlist.
- An activity log for account changes, publication decisions, candidate-stage changes, application deletions and CV downloads. Log retention, database encryption, administrative MFA/SSO, central monitoring and disaster recovery are deployment responsibilities. The application does not claim an ISO certification or legal compliance certification.

## Production hosting

The local launcher is a development preview. For live recruitment, deploy the **Python application and persistent private storage**, rather than uploading only the HTML files to static hosting. Nginx/Apache can reverse-proxy to Gunicorn on a Linux host. Cloudflare Pages/Vercel static hosting alone does not run this Flask/SQLite application.

1. Install Python 3.10+, the pinned dependencies and ClamAV. Keep virus definitions current. Run the service under a dedicated unprivileged user, with a writable private data directory outside the public directory. Restrict the application port to loopback/private traffic. Use one application instance on one host for the included SQLite storage design; use PostgreSQL and private object storage before adopting multi-host scale.
2. Set `ATS_ENV=production`, `ATS_PUBLIC_ORIGIN` to your exact HTTPS origin, `ATS_DATA_DIR` to the private persistent directory and `ATS_CLAMSCAN` to the absolute scanner executable. Production startup refuses missing HTTPS-origin or scanner configuration. Create the first administrator using `python manage.py create-admin`. No application secret is required because authentication uses random opaque database-backed session tokens, not signed client-side session contents.
3. From the backend directory, run `gunicorn --bind 127.0.0.1:8765 --workers 2 --timeout 60 wsgi:app` under your service manager. Terminate TLS at the reverse proxy; preserve the original Host header. Permit request bodies of 10 MB and allow at least 60 seconds for CV scanning. The configured public origin must match the actual browser origin exactly.
4. For **exactly one trusted reverse proxy**, set `ATS_TRUST_PROXY=1` and have that proxy overwrite X-Forwarded-For and X-Forwarded-Proto. Keep Gunicorn unreachable directly. Otherwise leave it unset. This matters because throttling uses client IP addresses. Do not forward arbitrary, user-controlled proxy chains.
5. Verify production scan success, HTTPS secure-cookie behaviour, account creation/reset, ownership boundaries, approval-only publication, CV download, backup/restore and privacy requests on the deployed host. Complete a hosting security review before collecting real applications. Application-layer tests do not verify a future host's TLS, firewall, file permissions or scanner installation.

Minimal Nginx location behind an already configured HTTPS server:

```nginx
location / {
    proxy_pass http://127.0.0.1:8765;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    client_max_body_size 10m;
    proxy_read_timeout 60s;
}
```

Do not expose a separate Nginx `root` that includes the backend or private data. The Flask server deliberately serves only public HTML, approved asset types and the existing office-map iframe. Keep the existing ERP preview disabled until its own authentication adapter is implemented; the ATS does not silently connect it to recruiter credentials.

## Recovery, retention and release operations

- Additional administrator: from backend, run `python manage.py create-admin`. The command prompts for name, email and password.
- Lost password: run `python manage.py reset-password`. Supply the account email and a new temporary password interactively; existing sessions are revoked and a change is required at sign-in. This is an operator function requiring private server access.
- Backup: stop the application, then run `python manage.py backup --destination /absolute/private/new-backup-directory`. This uses SQLite's backup API and copies the CV directory. The destination must be new and outside the website. Encrypt and restrict backups. Test restoration before relying on them.
- Restore: stop the application, restore `ats.sqlite3` and the matching `resumes` directory into the configured private data directory, restore restrictive permissions and restart. Backups include password hashes and session rows; revoke sessions after restoration with the database operator if necessary.
- Retention: the deployment owner must approve a retention schedule appropriate to recruitment and legal obligations. This release does not silently expire candidate records. Review records periodically and use administrator deletion to fulfil approved deletion/withdrawal requests. Apply equivalent retention to backups. Keep the published privacy notice aligned with the chosen policy before launch.
- Tests: `python -m unittest discover -s tests -v` from backend. Tests use temporary databases and synthetic documents, not production data.
- Release: run `python backend/package_release.py` from the website folder. It excludes private storage, environments, caches, secrets and test runtime data. Distribute the resulting ZIP, not the live data folder. A SHA256 manifest is included.

## API handover

All write requests require a CSRF token returned by `GET /api/ats/v1/session` in `X-CSRF-Token`, with the same-origin session cookie. JSON requests use Content-Type application/json. Candidate submissions use multipart/form-data. Authenticated access and record scope are enforced on the server, regardless of interface visibility.

| Method / path under `/api/ats/v1` | Purpose / access |
|---|---|
| GET `/session`, `/options` | Session token, signed-in identity, allowed enum values |
| POST `/login`, `/logout`, `/password` | Recruitment authentication and password change |
| GET `/jobs`, `/jobs/{reference}` | Public approved open vacancies; filters and pagination |
| POST `/jobs/{reference}/applications` | Candidate application and private CV upload |
| GET / POST `/staff/jobs` | Scoped vacancy list / create draft |
| PUT `/staff/jobs/{id}` | Edit draft; invalidates publication approval |
| POST `/staff/jobs/{id}/transition` | Submit, approve, return or close; approve/return administrator-only |
| GET `/staff/applications` | Scoped and paginated applicant list |
| GET `/staff/applications/{id}` | Profile, history, notes and permitted next stages |
| POST `/staff/applications/{id}/stage`, `/notes` | Stage changes and private notes |
| GET `/staff/applications/{id}/cv` | Authorised attachment download |
| DELETE `/staff/applications/{id}` | Administrator-only deletion of profile, history, notes and CV |
| GET / POST `/staff/users` | Administrator account list / creation |
| PATCH `/staff/users/{id}` | Administrator role/access changes |
| POST `/staff/users/{id}/reset-password` | Administrator temporary-password replacement |
| GET `/staff/audit` | Administrator activity log, latest 150 records |

Public health endpoint: `/api/health`. Role permissions do not extend to HR/payroll records in the separate ERP preview. Integration with that ERP, enterprise SSO, email delivery, candidate self-service accounts and automated CV parsing are not implemented in this release.

Implementation references: [Flask web security](https://flask.palletsprojects.com/en/stable/web-security/), [Flask upload patterns](https://flask.palletsprojects.com/en/stable/patterns/fileuploads/), [OWASP File Upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [OWASP Authentication guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).
