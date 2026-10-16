# Frontend and Backend Integration Handover

The package is a static website. It contains no secrets, production credentials, database or live ERP authentication. Browser previews do not send form POSTs or store passwords.

## Configuration

js/site-config.js contains the verified brand/email and empty values for phone, address, licence, MoHRE registration, TRN and backend endpoints. Empty endpoint fields are intentional. Setting a URL alone does not activate the preview handlers; implement and review the adapter first.

## RFP endpoint

Suggested route: `POST /api/v1/rfp`, `multipart/form-data`.

Suggested fields: clientEntity, contactName, workEmail, lpoReference, category, headcount, emirate, urgency, scope, commercialModel, consent and up to five documents.

Categories also include `corporate` and `it-erp`. Workforce headcount is disabled and excluded for these project types. Corporate enquiries add businessJurisdiction and approvalScope. HR consultation/HRMS enquiries add erpScope, currentSystem, targetSystem and systemUsers; the last three are optional. The legacy `it-erp` value and it-erp-consulting.html URL are retained for navigation compatibility, while public wording is HR consultation and HRMS/ERP techno-functional services. Validate all category-specific requirements again on the server.

`recruitment` and `headhunting` provide separate direct-hire/search entry routes with position-oriented scope guidance and required appointment count. Existing `professional` and `industrial` values remain compatible with the temporary-staffing and manpower-deployment routes. The service taxonomy distinguishes candidate placement from agency-employed staffing and EOR administration.

The local preview validates required fields and file extensions, maximum count 5 and maximum 10 MB per file. These checks improve UX only. The backend must independently validate and sanitise data, verify file MIME/signature, scan uploads, enforce size/count limits, apply spam/rate limits and define access/retention. Use TLS and appropriate origin/CSRF protection. Return a real receipt reference only after persistence succeeds.

The preview currently creates a local summary and download. Files are not uploaded; the brief records filenames, sizes and types without contents. The email link opens an explicit draft to info@tawreed.org and tells the user to attach files separately. Rendering uses textContent rather than injecting input as HTML.

## ERP authentication

Suggested route: `POST /api/v1/auth/login`. Example request shape:

```json
{"identity":"assigned employee ID or work email","password":"in-memory only","role":"employee|client|staff","rememberDevice":false}
```

All pages contain `<!-- ERP AUTH ENDPOINT HOOK: action="/api/v1/auth/login" -->` guidance near the form. The actual preview has no GET form action and no password name attribute. Form fields are disabled without JavaScript. The JS handler prevents submission, clears the password and explains that access is not enabled.

For production: use the approved IdP/ERP, server-side role authorisation, secure HttpOnly SameSite cookies, session expiration, rate limiting, lockout, MFA where required, CSRF/origin protection and audit logging. Never trust the selected frontend role as authorisation. Never store passwords, access tokens or sensitive employee records in localStorage. Remember-device policy belongs to the identity provider.

## Password reset and SSO

Suggested reset route: `POST /api/v1/auth/password-reset`. Use uniform responses, short-lived tokens and verified delivery; do not disclose whether an identity exists.

Suggested SSO start routes: `/api/v1/auth/uae-pass/start` and `/api/v1/auth/microsoft/start`. Keep OAuth/OIDC secrets on the server, verify redirect URLs/state/nonce and handle callbacks server-side. UAE PASS requires the appropriate provider onboarding. Microsoft 365 requires the approved tenant/app configuration. The current buttons only show clear status messages.

## Deployment and data boundaries

- Serve on HTTPS; use CSP, safe response headers, secure cookies and a controlled dependency policy appropriate to the backend.
- The complete design is in css/site.css. Remove the development CDN snippet or replace it with a pinned compiled build for production.
- The service-area iframe is a local schematic, not an assertion of an office location. Replace it with a map only after the real address/coordinates and embedding/privacy requirements are confirmed.
- Obtain approval of privacy wording, retention, business contact details and legal identity before collecting real production enquiries.

## QA scope

The audit covers internal targets and fragments, basic markup structure, image loading, local font loading, layout widths, JS errors and principal interactions. Browser testing uses Chrome at 320, 375, 768 and 1440 px. It is not a full WCAG conformance assessment, security penetration test or proof of every email client/browser combination. External source URLs were reviewed for research; automated offline audit does not certify their future availability.

## Current service and content structure

The eight-service carousel is in `js/main.js` and uses a native horizontal scroll track, responsive card widths, previous/next wrap, pagination and keyboard navigation. All eight requested anchors exist. Four service detail pages are linked from the services overview; operational chapters are visible without a content-tab script.

Additional accepted form categories are `payroll`, `hospitality-fm`, `overseas` and `advisory`. The advisory route does not require workforce headcount. Corporate and HR systems conditional fields retain their existing behaviour. The backend must revalidate the category-specific schema and all attachments.

Image fallback in `js/enhancements.js` permits photographs on direct file previews when internet is available. It switches to local artwork on image error or offline status. Branding remains local. Tailwind preflight and container plugins are disabled to protect the established local layout.
