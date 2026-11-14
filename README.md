# Documentation claim auditor

An offline static auditor comparing documentation promises with recognized source calls. It uses only the standard library, parses source without executing it, makes no network calls, and writes no reports or project files. Requires CPython 3.9 or newer.

## Installation and usage

```sh
python3 -m pip install .
carte-grise-extraction-claim-audit audit .
carte-grise-extraction-claim-audit audit . --json --verbose --ignore build --ignore dist --fail-on medium
python3 -m carte_grise_extraction_claim_audit audit .
carte-grise-extraction-claim-audit --version
python3 -m unittest discover
```

The repository defaults to the current directory. Repeatable ignore prefixes are relative paths matched by path components. Thresholds are lowercase high or medium; the default is high. Exit 0 means PASS at the selected threshold, exit 2 means findings at that threshold, and exit 1 means usage or I/O error. JSON contains verdict, findings with rule, severity, message and locations, and separate production and test evidence. Verbose text includes evidence locations.

## Matching rules

Root README.md and Markdown files with a docs path component are scanned. Backtick and tilde fences with up to three leading spaces are excluded; inline code counts. Paragraphs split on blank lines. Normalization lowercases, expands contractions, replaces hyphens with spaces, and collapses whitespace. Exact word-boundary matches prefer longest phrases with alphabetical ties. Denial spans are removed before positive matching. Each family emits at most one finding.

Source is parsed with AST, never executed. Symlinked files and directories are excluded. Files under fixtures, docs and examples supply no evidence. Tests count separately. Syntax-invalid files supply no evidence. Each route must occur within a single module. Local function, method and class definitions shadow matching route names. Assignments, annotated assignments and context-manager bindings shadow imported names. Generic attributes allow any base; bare calls require an imported recognized name. A positive promise without source fails, while a denial without source passes. Test-only evidence gives a medium finding. Dead code counts; untraced alias chains are missed. This is static pattern matching rather than semantic judgement. Denial handling depends on the exact denial vocabulary.

## Reference data

The following fenced reference documents the checked vocabulary, routes, exclusions, and matching hazards. It describes the checked feature, rather than capabilities of this auditor.

```text
carte grise extraction
extract carte grises
extracts carte grises
extracting carte grises
extract carte grise
extracts carte grise
extracting carte grise
carte grise parsing
carte grise parser
parse carte grises
parses carte grises
parse carte grise
parses carte grise
carte grise scanning
carte grise scanner
scan carte grises
scans carte grises
scan carte grise
scans carte grise
vehicle registration certificate extraction
extract vehicle registration certificates
extracts vehicle registration certificates
extracting vehicle registration certificates
extract vehicle registration certificate
extracts vehicle registration certificate
extracting vehicle registration certificate
vehicle registration certificate parsing
vehicle registration certificate parser
parse vehicle registration certificates
parses vehicle registration certificates
parse vehicle registration certificate
parses vehicle registration certificate
vehicle registration certificate scanning
vehicle registration certificate scanner
scan vehicle registration certificates
scans vehicle registration certificates
scan vehicle registration certificate
scans vehicle registration certificate
registration certificate extraction
extract registration certificates
extracts registration certificates
extracting registration certificates
extract registration certificate
extracts registration certificate
extracting registration certificate
registration certificate parsing
registration certificate parser
parse registration certificates
parses registration certificates
parse registration certificate
no carte grise extraction
does not extract carte grises
does not extract carte grise
does not support carte grise extraction
without carte grise extraction
no carte grise parser
does not parse carte grises
does not parse carte grise
no vehicle registration certificate extraction
does not extract vehicle registration certificates
does not extract vehicle registration certificate
does not support vehicle registration certificate extraction
without vehicle registration certificate extraction
no carte grise scanner
does not scan carte grises
does not scan carte grise
no registration certificate extraction
does not extract registration certificates
does not extract registration certificate
without registration certificate extraction
no registration certificate parser
does not parse registration certificates
does not parse registration certificate
carte grise extraction not supported

documented-carte-grise-extraction-claim-false HIGH (MEDIUM for test-only evidence)
documented-no-carte-grise-extraction-claim-false HIGH

Generic names:
extract_carte_grise
extract_carte_grises
parse_carte_grise
parse_carte_grises
extract_vehicle_registration_certificate
parse_vehicle_registration_certificate
extract_registration_certificate
parse_registration_certificate
extract_carte_grise_data
parse_carte_grise_data
carte_grise_extraction
carte_grise_extractor
carte_grise_parser
vehicle_registration_certificate_extraction
vehicle_registration_certificate_extractor
vehicle_registration_certificate_parser
extract_carte_grise_info
parse_carte_grise_info
carte_grise_scan
carte_grise_scanner
scan_carte_grise
scan_carte_grises
extract_registration_certificate_data
parse_registration_certificate_data

mindee Client construction + parse call passing CarteGriseV1 (Name
exactly CarteGriseV1, or Attribute with attr exactly CarteGriseV1 such
as product.CarteGriseV1 / mindee.product.fr.CarteGriseV1 /
mindee.v1.product.fr.CarteGriseV1) as any argument; import gate
mindee. CarteGriseV1 exists in BOTH mindee 4.x and 5.x (4.22.0 wheel
inspected 2026-11-14: mindee/product/fr/carte_grise/carte_grise_v1.py
defines class CarteGriseV1(Inference), endpoint_name
"carte_grise", endpoint_version "1", exported via
mindee.product.fr — NOT at the top-level mindee.product namespace;
its document is "Carte Grise API version 1.1" with fields a
(license plate number), b (first release date), c1 (owner full
name including maiden name), c3 (owner address), c41 (number of
owners of the license certificate), c4a (mentions about the
ownership of the vehicle), d1 (brand), d3 (commercial name), e
(VIN), f1 (maximum admissible weight), f2 (maximum admissible
weight within the license's state), f3 (maximum authorized weight
with coupling), formula_number, g (weight with coupling if tractor
different from category M1), g1 (national empty weight), i (car
registration date of the given certificate), j (category), j1
(national type), j2 (body type, CE), j3 (body type, national
designation), mrz1, mrz2, owner_first_name, owner_surname, p1
(engine displacement, cm3), p2 (maximum net power, kW), p3 (fuel
type or energy source), p6 (administrative power, fiscal
horsepower), q (power to weight ratio), s1 (number of seats), s2
(number of standing rooms), u1 (sound level, dB), u2 (engine
rotation speed, RPM); 5.4.0 wheel inspected 2026-11-14 still
contains it at mindee/v1/product/fr/carte_grise/carte_grise_v1.py
with the same class name, endpoint name, and version). The tool
detects the call in source, not the installed SDK version. A parse
call passing any other product (InvoiceV4, ReceiptV5, PassportV1,
FinancialDocumentV1, BankCheckV1, BankAccountDetailsV2, PayslipV2,
PayslipV3, HealthcareCardV1, BusinessCardV1, CustomV1, GeneratedV1,
BillOfLadingV1, ResumeV1, DeliveryNoteV1, DriverLicenseV1, IdCardV1,
InternationalIdV2, EnergyBillV1, or any other) is NOT evidence.

## veryfi names (implementation MUST match exactly)

NO veryfi route: veryfi has no carte grise method in the Python SDK.
The 5.1.0 wheel, inspected 2026-11-14, contains zero hits for
"grise", "vehicle", or "registration" across all .py files, so a
veryfi call of ANY kind is NOT evidence. A call to the non-existent
process_carte_grise_document / process_carte_grise_document_url counts as
nothing. A raw HTTP call to
"https://api.veryfi.com/api/v8/partner/documents" is NOT evidence
either: it is Veryfi's generic documents endpoint, shared by
receipts, invoices, and other documents alike.

## azure names (implementation MUST match exactly)

NO azure route: Azure Document Intelligence has no carte grise or
vehicle registration model. The Microsoft Learn v4.0 (GA) page,
opened and searched 2026-11-14, contains zero hits for "carte
grise" and zero hits for "vehicle registration". A
begin_analyze_document call with ANY model id is NOT evidence —
including prebuilt-idDocument, which covers driver's licenses
and passports, not vehicle registration certificates.

## google document ai names (implementation MUST match exactly)

NO Google Document AI route: the Document AI processors list page,
opened and searched 2026-11-14, contains zero hits for
"Vehicle Registration" and zero hits for "Carte Grise" — there is
no vehicle registration or carte grise processor, so a
process_document call with ANY processor is NOT evidence.

## eden ai / llamaparse / nanonets / docsumo / carsxe / other vendor names (implementation MUST match exactly)

NO Eden AI route: Eden AI documents no carte grise parser
model, so a universal-ai call with ANY model id is NOT evidence.
NO LlamaParse route: LlamaParse is a generative parsing API with
no fixed static fingerprint naming carte grise. NO Nanonets route:
Nanonets document calls carry an opaque model_id in the URL path
(no fixed fingerprint — the model id is user-configured, not a
carte grise product). NO Docsumo route: Docsumo uploads go to a
generic endpoint with the document type configured in the
dashboard, not in the call. NO ABBYY Vantage / Rossum / Klippa /
Parseur / Extend route: opaque skill / queue / template / workflow
IDs. NO Textract route: Textract has no carte grise or vehicle
registration operation (AnalyzeID covers driver's licenses and
passports). NO CarsXE route: vin_ocr / plate_image_recognition /
plate_decoder / specs are VIN / plate lookups from a photo or a
plate string, not extraction of fields from a carte grise
document. NO DocuPipe / Konfuzio / RPACPC / Wintone route: opaque
REST endpoints with no fixed static fingerprint naming carte
grise in Python source. NO mindee v2 extraction API route:
configurable model id, no fixed fingerprint.

## Documented matching hazards (honest limitations, also for the README)

- The bare phrases "carte grise extraction" / "extract carte
  grise" / "extract carte grises" are deliberately
  CARTEGRISEEXTRACTION phrases: in document-tool docs they almost
  always name carte grise extraction. But "carte grise" can
  also name a carte grise the tool merely stores, displays, or
  manages (a carte grise archive, a carte grise template
  library) without extracting fields from a carte grise
  document: a doc that means storing, displaying, or templating
  carte grises, not extracting fields from them, is a false
  positive; the tool flags the claim, only the code decides.
- "carte grise parsing" / "carte grise parser" are deliberately
  phrases: a doc can say "carte grise parser" about a tool that
  only renders a carte grise as formatted text, or a "carte grise
  parser" that is really a keyword highlighter over plain
  text. The tool flags the claim; only the code decides.
- "carte grise scanning" / "scan carte grise(s)" are
  deliberately phrases: "scanning" a carte grise can mean merely
  photographing it or OCRing it into raw text, with no structured
  field extraction. The tool flags the claim; only the code decides.
- "vehicle registration certificate extraction" / "extract vehicle
  registration certificate(s)" / "vehicle registration certificate
  parsing" / "vehicle registration certificate parser" are
  deliberately phrases: a carte grise IS the French vehicle
  registration certificate, so the English name names the same
  document. A doc that merely mentions vehicle registration
  certificates as document types it stores is a false positive;
  the tool flags the claim, only the code decides.
- "registration certificate extraction" / "extract registration
  certificate(s)" / "registration certificate parsing" /
  "registration certificate parser" are deliberately phrases:
  "registration certificate" also names other certificates
  (company registration, birth registration) in other domains.
  A doc that means a different "registration certificate" is a
  false positive; the tool flags the claim, only the code decides.
- "carte grise data extraction" / "extract carte grise data" /
  "carte grise field extraction" are deliberately phrases: a doc
  can mean extracting plain text from a carte grise, not
  structured fields. The tool flags the claim; only the code
  decides.
- The French phrase "certificat d'immatriculation" (and its
  extraction / parsing / scanning variants) is deliberately NOT
  in the phrase lists: the matcher does exact phrases after a
  normalisation that does not strip apostrophes, so a French
  apostrophe phrase would match unreliably across docs that
  write it with a straight quote, a curly quote, or no
  apostrophe at all. A doc that claims extraction using only the
  French name is missed; the English "carte grise" and "vehicle
  registration certificate" phrases are the checked ones. Say so
  in the README.
- CarteGriseV1 v1.1 carries the field set listed in the mindee
  names section above (plate, owner, VIN, brand, weights, dates,
  MRZ, engine, seats, and the rest): it has NO insurance, NO
  technical inspection (controle technique), and NO lien /
  gage status fields. A tool that extracts those does so through
  some other route; this family checks for the CarteGriseV1
  call, not for those fields. Say so in the README.
- A generic `extract_carte_grise(` / `parse_carte_grise(` /
  `extract_registration_certificate(` call can name a string
  parser for text the user typed in rather than a document
  extractor: the tool counts the call, the claim plus the code
  decide — and a subprocess call invoking an external CLI is NOT
  evidence by design, so a thin wrapper that only calls
  subprocess fails.
- Mindee `parse` with CarteGriseV1 counts as evidence:
  CarteGriseV1 exists in mindee 4.22.0 AND 5.4.0 (both wheels
  inspected 2026-11-14). The tool detects the call in source,
  not whether the call succeeds against a current API version.
  Say so in the README.
- Mindee `parse` with CarteGriseV1 is NOT a 4.x-only fingerprint:
  unlike the delivery note / bill of lading / resume products,
  mindee 5.x kept the off-the-shelf carte grise product (5.4.0
  wheel inspected 2026-11-14 — mindee/v1/product/fr/carte_grise/
  still defines CarteGriseV1 with endpoint "carte_grise" v1).
  Say so in the README.
- Mindee `parse` with InvoiceV4 / ReceiptV5 / PassportV1 /
  FinancialDocumentV1 / BankCheckV1 / BankAccountDetailsV2 /
  PayslipV2 / PayslipV3 / HealthcareCardV1 / BusinessCardV1 /
  CustomV1 / GeneratedV1 / BillOfLadingV1 / ResumeV1 /
  DeliveryNoteV1 / DriverLicenseV1 / IdCardV1 /
  InternationalIdV2 / EnergyBillV1 is NOT detected: those are
  other document types. Say so in the README.
- Mindee `parse` with DriverLicenseV1 is NOT detected: a driver's
  license is a different document from a carte grise. Say so in
  the README.
- Azure `begin_analyze_document` with ANY model id is NOT
  detected: Azure Document Intelligence has no carte grise or
  vehicle registration model (the Learn v4.0 GA page contains
  zero hits for "carte grise" and zero hits for "vehicle
  registration", verified 2026-11-14) — including
  prebuilt-idDocument, which covers driver's licenses and
  passports. Say so in the README.
- Veryfi calls of ANY kind are NOT detected: veryfi has no carte
  grise method (5.1.0 wheel inspected 2026-11-14 — the words
  "grise", "vehicle", and "registration" do not appear anywhere
  in the wheel), and its document APIs post to a generic
  documents endpoint shared across document types. Say so in the
  README.
- Google Document AI `process_document` / `batch_process_documents`
  with ANY processor is NOT detected: Document AI has no vehicle
  registration or carte grise processor (the processors list
  page contains zero hits for "Vehicle Registration" and zero
  hits for "Carte Grise", verified 2026-11-14). Say so in the
  README.
- Eden AI universal-ai calls with ANY model id are NOT detected:
  Eden AI documents no carte grise parser model. Say so in the
  README.
- LlamaParse calls are NOT detected: its parsing API is
  generative with no fixed static fingerprint naming carte
  grise. Say so in the README.
- CarsXE calls are NOT detected: vin_ocr / plate_image_recognition
  / plate_decoder are VIN / plate lookups from a photo or a plate
  string, not extraction of fields from a carte grise document.
  Say so in the README.
- DocuPipe / Konfuzio / RPACPC / Wintone calls are NOT detected:
  opaque REST endpoints with no fixed static fingerprint naming
  carte grise in Python source. Say so in the README.
- Nanonets / Docsumo / ABBYY Vantage / Rossum / Klippa / Parseur /
  Extend calls are NOT detected: opaque model / skill / queue /
  template / workflow IDs, or a generic upload endpoint with the
  document type configured outside the call — no fixed fingerprint.
  Say so in the README.
- Textract `analyze_document` / `analyze_expense` / `analyze_id` /
  `start_document_analysis` / `get_expense_analysis` are NOT
  detected: generic document, expense, and identity analysis are
  not carte grise extraction, and Textract has no carte grise or
  vehicle registration operation. Say so in the README.
- A hand-rolled extraction from OCR text (`re.search` /
  `re.findall` on extracted text plus manual field assembly, no
  listed call) is NOT detected: the tool requires a listed call.
  Say so in the README.
- The mindee CLI, the veryfi CLI, and any other external carte
  grise tool invoked through subprocess are NOT detected:
  subprocess calls invoking an external CLI are NOT evidence by
  design. Say so in the README.
- Azure Document Intelligence, Mindee, and Veryfi are cloud APIs:
  the tool detects the client call in source, not whether
  credentials are configured or the call succeeds. Say so in the
  README.
- "extract carte grise text" / "extract text from carte grise"
  claims are NOT in the phrase lists: extracting plain text
  from a carte grise is text extraction, not carte grise
  field extraction. Say so in the README.
- "carte grise template" / "carte grise form" claims are NOT
  in the phrase lists: templating or form-filling a carte grise
  is creating one, not extracting fields from one. Say so in the
  README.
- "carte grise tracking" / "carte grise status" claims are
  NOT in the phrase lists: tracking a vehicle by its carte grise
  number is downstream of extraction, not extraction
  itself. Say so in the README.
- "proof of delivery extraction" / "packing list extraction" /
  "vehicle registration lookup" / "plate recognition" /
  "VIN decoding" claims are NOT in the phrase lists: proofs of
  delivery, packing lists, and plate / VIN lookups are different
  operations from carte grise document extraction. Say so in the
  README.
- "driver license extraction" / "passport extraction" claims are
  NOT in the phrase lists: a driver's license and a passport are
  different documents from a carte grise. Say so in the README.
- Invoice extraction claims ("extract invoices", "invoice
  extraction"), receipt extraction claims ("extract receipts",
  "receipt extraction"), ID document extraction claims ("extract
  passports", "passport extraction"), bank check extraction claims
  ("extract bank checks", "check extraction"), bank statement
  extraction claims ("extract bank statements", "statement
  extraction"), tax form extraction claims ("extract tax forms",
  "extract w2 forms", "1099 extraction"), pay stub extraction
  claims ("extract pay stubs", "payslip extraction"), health
  insurance card extraction claims ("extract health insurance
  cards", "health insurance card extraction"), business card
  extraction claims ("extract business cards", "business card
  extraction"), credit card extraction claims ("extract credit
  cards", "credit card extraction"), contract extraction claims
  ("extract contracts", "contract extraction"), mortgage
  extraction claims ("extract mortgages", "mortgage extraction"),
  resume extraction claims ("extract resumes", "resume
  extraction"), bill of lading extraction claims ("extract
  bills of lading", "bill of lading extraction"), and delivery
  note extraction claims ("extract delivery notes", "delivery
  note extraction") are NOT in the phrase lists: this family
  covers carte grises only. Say so in the README.
- As with every family: static pattern matching, not semantic
  judgement; dead code counts; alias chains the tracer cannot follow
  are missed; exact phrases only, not semantics; denial handling
  depends on the denial phrase list; each route must sit in a single
  module.

```
