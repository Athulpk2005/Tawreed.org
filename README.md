# Tawreed — restored and enriched website

Unzip this package and open `index.html` in a modern browser. No installation or server is required. Photographs load when internet is available; included local illustrations replace unavailable images. All essential styles, scripts, fonts and original logos are local.

## What changed

The earlier Expanded website is the visual base: its opening headline, full primary logo, typography, page banners, corporate palette, shared navigation and multi-page structure are retained. The homepage now contains the eight requested image-led service segments, with explicit next/previous arrows, responsive pagination and native mobile swiping.

Detailed content is visible in editorial sections and operational chapters. It is not hidden behind content tabs. Four additional service detail pages preserve the full methods while keeping the main services page navigable. Administration and the commercial decision framework also have separate pages. Corporate setup and techno-functional HR/HRMS services remain available.

## Eight core service routes

| Segment | Homepage destination | Further detail |
|---|---|---|
| White-collar & professional staffing | `services.html#white-collar` | `professional-staffing.html` |
| Industrial, logistics & blue-collar deputation | `services.html#blue-collar` | `industrial-manpower.html` |
| EOR & PEO | `eor-payroll.html#eor` | Same page, complete employment architecture |
| WPS & managed payroll | `eor-payroll.html#payroll` | Same page, SIF, reconciliation, benefits and funding |
| Emiratisation | `emiratisation.html` | National talent, current regulatory context and retention |
| Facilities & hospitality manpower | `services.html#hospitality-fm` | `facilities-hospitality.html` |
| Volume mobilisation & international corridors | `services.html#overseas-corridors` | `international-mobilisation.html` |
| HR advisory, PRO & licensing | `about.html#governance` | HR process, transaction ownership, renewals and evidence |

Other pages: `corporate-services.html`, `it-erp-consulting.html`, `compliance-welfare.html`, `contact.html`, `portal-login.html`, `how-we-work.html`, `administration.html` and `commercial-framework.html`.

## Editing

All seventeen HTML pages are editable directly. The accepted earlier styling remains in `css/site.css`; new carousel and visible-content components are in `css/service-enhancements.css`. `js/main.js` contains the mobile menu, portal, form, calculator, scenarios and eight-service carousel. `js/enhancements.js` handles image fallback and the welfare/visual carousels. `assets/service-catalogue.json` is a service-route reference; the visible cards are ordinary editable HTML.

The Tailwind configuration disables preflight and the container plugin. More-specific local container rules keep the established spacing intact if the CDN loads later. The website does not depend on the CDN for its visual baseline.

## Branding

The primary horizontal full-colour lockup remains in the header, including the original centred descriptor and two-tone w. The supplied T identifier is used for section demarkers, image-card badges, list markers, subtle card watermarks and icons. The original reverse lockup is used in the dark footer. All native variants are in `assets/brand/`.

The supplied Flow logo pack contains raster artwork rather than editable vector paths. High-resolution original PNGs are used proportionally; no altered colours, recreated gradient or fabricated vector reconstruction is substituted. Code-native line icons and offline SVG illustrations are separate from the logo assets.

## Commercial and credential wording

The 3–5-working-day local and 18–25-working-day overseas mobilisation windows are planning targets with readiness dependencies. The 90-day replacement provision is defined by the signed engagement terms. Relief capacity, support coverage, facilities, funded gratuity or escrow mechanisms and authority approvals require the actual agreed operating arrangement. No historical performance, owned fleet/camp, ISO certificate, Nafis partnership, supplier pre-qualification or ICV score is invented.

Current regulatory and standards references are documented in `docs/`. ISO 9001:2015 is identified as a legacy edition rather than presented as the current edition or a Tawreed certification. Tawreed.org is the corporate domain, not a government procurement authority.

## Functional boundary

The portal is an integration preview. Login, reset, UAE PASS and Microsoft SSO do not send or store credentials. The RFP form validates and prepares a local downloadable brief with attachment metadata; files are not uploaded. Backend/HRMS integration hooks remain documented in the source and integration guide.

Confirmed email: info@tawreed.org. Phone, registered office, licence numbers and TRN remain unpublished pending verified details, as instructed.

## Validation and packaging

Run `python3 tools/verify_website.py` to check relative links, fragments, markup, labels and local assets. Run `python3 tools/package_website.py` to verify and regenerate `Tory_Workforce_Solutions_Website.zip` with checksums. These tools use Python’s standard library.

Browser reports cover seventeen pages at four sizes, portal/form/calculator interactions, carousel wrap/pagination, native mobile swipe, visible content and online/offline image handling. These checks are functional QA, not certification or a full accessibility/security assessment.

## Additive visual edition — 16 October 2026

The approved content is preserved in full across all seventeen pages. New visual styling and interactions are isolated in `css/visual-enrichment.css` and `js/visual-enrichment.js`. The homepage has a manual three-image photographic backdrop, the eight-service carousel remains, and inner pages gain framed imagery and editorial splits. Welfare thumbnails extend the original four-slide gallery. Only free Unsplash imagery is used, with local fallback artwork. See `docs/VISUAL_ENRICHMENT.md` for the visual source register and content-preservation audit.
