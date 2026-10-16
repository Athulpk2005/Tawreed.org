# Additive visual edition — 16 October 2026

The seventeen-page website was enriched in place. The original base styles, enhancement styles, main interaction script, existing enhancement script, site configuration and original brand artwork remain byte-for-byte unchanged. New art direction is isolated in `css/visual-enrichment.css` and `js/visual-enrichment.js`.

## Content preservation

`VISUAL_CONTENT_PRESERVATION.json` compares every original visible text node in document order, all original headings, links, identifiers, tables, form-field attributes and ERP integration comments against the retained pre-edit website. It records 28,925 original words across seventeen root pages, including repeated navigation/legal text. The baseline copy, citations, workflows and matrices remain intact. Layout wrappers and image layers are additive; none of the original pages were replaced by a reduced-content template.

## Visual treatments

- Homepage: three manually controlled photographic backdrops behind the unchanged approved hero copy; previous/next, pagination, keyboard and touch controls; a restrained four-icon governance-theme strip; original eight-service carousel retained; visual corporate/HRMS cards and a small national-talent/scenario feature.
- Inner pages: framed photographic hero panels, responsive editorial text/image splits and panoramic workflow images. Existing typographic hero identifiers remain visible over their photograph panels.
- Brand: indigo/periwinkle/teal artwork preserved; original T tiles supply decorative card/standard watermarks, badges and CTA accents. These marks do not represent certification.
- Services: professional interviews/meetings, technical work, managed deployment and reception imagery contextualise the four service sections without shortening the original text.
- EOR/payroll: technical processing illustration and a restrained calculator glow with an “Illustrative fee model” label. No unsupported 100% WPS history or audit-proof certification claim was added.
- Welfare: all four original gallery slides and captions remain. Added thumbnail controls stay synchronised with the original arrows. Accommodation, dining, recreation and transport are illustrative, not evidence of owned facilities, space/AC standards or a private fleet.
- Portal: branded data-centre side panel and lock graphic. The SSO label states integration is planned. The original preview notice, authentication/reset/SSO boundary and API hooks remain intact; no unverified 256-bit encryption or live authentication badge was introduced.
- Cases: photographs and original T identifiers enhance the existing illustrative scenarios on `how-we-work.html`. No client avatar or testimonial is fabricated.

## Photography source policy

Only free Unsplash sources are referenced; no AI image generation or paid Unsplash+ assets were used for this edition. Public URLs use `auto=format&fit=crop&w=1000&q=80`. Browser error handling falls back to the existing local SVG artwork, and hides an image only if that fallback also fails. Hero images are prioritised; supporting imagery is lazy-loaded.

Stock photographs do not establish the nationality, employer, certification or location of the people shown. The precise free Kandura-and-Abaya corporate boardroom composition was not verified, so it was not fabricated or mislabelled. Free corporate teams, regional business context, actual Dubai architecture and accurately described healthcare/hospitality/technical photographs supply the visual context. No photograph represents a Tawreed employee, owned camp, vehicle fleet or office.

The standard Unsplash licence is recorded at https://unsplash.com/license. Photo captions avoid implied affiliation. Existing source records remain in `IMAGE_SOURCES.md`; new sources are listed below. Website copyright permission does not by itself prove model/property release status or allow an endorsement claim.

## Additional free source pages

| Subject | Photographer | Source page | CDN photo identifier |
|---|---|---|---|
| Business trainer presenting charts | Vitaly Gariev | https://unsplash.com/photos/man-presents-charts-to-seated-audience-in-a-modern-office-Nd7SpexkoNA | photo-1758691736508-a85d1f7d5a77 |
| Colleagues collaborating on a laptop | Kristina spremo | https://unsplash.com/photos/two-colleagues-collaborating-on-a-laptop-in-office-gbzcMKTGHqc | photo-1759844197486-5b3612c7d534 |
| Dubai Museum of the Future | Haris khan | https://unsplash.com/photos/museum-of-the-future-in-dubai-oF7dZYCgO3k | photo-1686918269961-507270a5a238 |
| Electronics engineers testing software | ThisisEngineering | https://unsplash.com/photos/engineers-working-in-automotive-factory-WjOWazUPAss | photo-1581091212991-8891c7d4bd9b |
| Mechanical engineer soldering circuitry | ThisisEngineering | https://unsplash.com/photos/person-holding-black-coated-wire-Q-UJHElsKOc | photo-1581090466144-8ed89ea98b25 |
| Industrial-flooring crew in technology centre | Craftsman Concrete Floors | https://unsplash.com/photos/workers-in-a-large-empty-warehouse-with-polished-floors-vp0ffQcBqJ0 | photo-1772300164438-f73307d3b645 |
| Healthcare professionals in headscarves | Divaris Shirichena | https://unsplash.com/photos/two-women-in-hijabs-standing-in-a-dental-office-q0Jp95WVu-s | photo-1685022036574-12bffde5e2b7 |
| Reception professional with a tablet | Bluestonex | https://unsplash.com/photos/woman-using-a-tablet-at-a-reception-desk-Li6MH3rfyPo | photo-1759143545924-beb85b33c0f1 |

## Validation and preview

See `VISUAL_CONTENT_PRESERVATION.json`, `VISUAL_IMAGE_AUDIT.json`, `VISUAL_BROWSER_AUDIT.json` and `VISUAL_ONLINE_AUDIT.json`. These complement the existing static verification report. Functional browser tests are not a formal legal, security or accessibility certification.

Extract `Tory_Workforce_Solutions_Website.zip` completely and open `tory-website/index.html`. All essential styles, fonts, logos, navigation and scripts remain local. An internet connection loads photographs; unavailable remote images fall back to local artwork.

The previous architecture handover describes the earlier static homepage hero. This edition adds the three-image hero layer and gallery thumbnails; its service routes, approved copy and backend boundaries remain unchanged.
