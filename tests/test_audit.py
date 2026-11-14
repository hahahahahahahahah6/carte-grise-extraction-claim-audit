import ast
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from carte_grise_extraction_claim_audit.audit import audit, module_evidence, claims
from carte_grise_extraction_claim_audit.__main__ import main
from carte_grise_extraction_claim_audit import phrases

EXPECTED_POSITIVE = ('carte grise extraction', 'extract carte grises', 'extracts carte grises', 'extracting carte grises', 'extract carte grise', 'extracts carte grise', 'extracting carte grise', 'carte grise parsing', 'carte grise parser', 'parse carte grises', 'parses carte grises', 'parse carte grise', 'parses carte grise', 'carte grise scanning', 'carte grise scanner', 'scan carte grises', 'scans carte grises', 'scan carte grise', 'scans carte grise', 'vehicle registration certificate extraction', 'extract vehicle registration certificates', 'extracts vehicle registration certificates', 'extracting vehicle registration certificates', 'extract vehicle registration certificate', 'extracts vehicle registration certificate', 'extracting vehicle registration certificate', 'vehicle registration certificate parsing', 'vehicle registration certificate parser', 'parse vehicle registration certificates', 'parses vehicle registration certificates', 'parse vehicle registration certificate', 'parses vehicle registration certificate', 'vehicle registration certificate scanning', 'vehicle registration certificate scanner', 'scan vehicle registration certificates', 'scans vehicle registration certificates', 'scan vehicle registration certificate', 'scans vehicle registration certificate', 'registration certificate extraction', 'extract registration certificates', 'extracts registration certificates', 'extracting registration certificates', 'extract registration certificate', 'extracts registration certificate', 'extracting registration certificate', 'registration certificate parsing', 'registration certificate parser', 'parse registration certificates', 'parses registration certificates', 'parse registration certificate')
EXPECTED_NEGATIVE = ('no carte grise extraction', 'does not extract carte grises', 'does not extract carte grise', 'does not support carte grise extraction', 'without carte grise extraction', 'no carte grise parser', 'does not parse carte grises', 'does not parse carte grise', 'no vehicle registration certificate extraction', 'does not extract vehicle registration certificates', 'does not extract vehicle registration certificate', 'does not support vehicle registration certificate extraction', 'without vehicle registration certificate extraction', 'no carte grise scanner', 'does not scan carte grises', 'does not scan carte grise', 'no registration certificate extraction', 'does not extract registration certificates', 'does not extract registration certificate', 'without registration certificate extraction', 'no registration certificate parser', 'does not parse registration certificates', 'does not parse registration certificate', 'carte grise extraction not supported')
EXPECTED_NAMES = ('extract_carte_grise', 'extract_carte_grises', 'parse_carte_grise', 'parse_carte_grises', 'extract_vehicle_registration_certificate', 'parse_vehicle_registration_certificate', 'extract_registration_certificate', 'parse_registration_certificate', 'extract_carte_grise_data', 'parse_carte_grise_data', 'carte_grise_extraction', 'carte_grise_extractor', 'carte_grise_parser', 'vehicle_registration_certificate_extraction', 'vehicle_registration_certificate_extractor', 'vehicle_registration_certificate_parser', 'extract_carte_grise_info', 'parse_carte_grise_info', 'carte_grise_scan', 'carte_grise_scanner', 'scan_carte_grise', 'scan_carte_grises', 'extract_registration_certificate_data', 'parse_registration_certificate_data')

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def put(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = main(list(args))
        return code, out.getvalue()

    def test_phrase_oracle(self):
        parsed = ast.parse(Path(phrases.__file__).read_text())
        literals = {n.targets[0].id: ast.literal_eval(n.value) for n in parsed.body if isinstance(n, ast.Assign)}
        self.assertEqual(literals['CARTEGRISEEXTRACTION'], EXPECTED_POSITIVE)
        self.assertEqual(literals['NOCARTEGRISEEXTRACTION'], EXPECTED_NEGATIVE)
        self.assertEqual(literals['GENERIC_NAMES'], EXPECTED_NAMES)
        self.assertEqual(phrases.CARTEGRISEEXTRACTION, EXPECTED_POSITIVE)
        self.assertEqual(phrases.NOCARTEGRISEEXTRACTION, EXPECTED_NEGATIVE)
        self.assertEqual(phrases.GENERIC_NAMES, EXPECTED_NAMES)
        self.assertEqual(len(set(EXPECTED_NAMES)), 24)

    def test_all_positive_phrases(self):
        for phrase in EXPECTED_POSITIVE:
            with self.subTest(phrase=phrase):
                self.assertTrue(claims(phrase)[0])

    def test_all_denials_suppress_positives(self):
        for phrase in EXPECTED_NEGATIVE:
            with self.subTest(phrase=phrase):
                positive, negative = claims(phrase)
                self.assertFalse(positive)
                self.assertTrue(negative)

    def test_longest_word_boundaries(self):
        self.assertEqual(claims('extract carte grises'), (['extract carte grises'], []))
        self.assertEqual(claims('preextract carte grisesuffix'), ([], []))
        self.assertEqual(claims("certificat d'immatriculation extraction"), ([], []))
        self.assertEqual(claims('does not extract carte grises. carte grise extraction')[0], ['carte grise extraction'])

    def test_good(self):
        self.put('README.md', 'We extract carte grises.')
        self.put('app.py', 'x.extract_carte_grise()')
        self.assertEqual(self.cli('audit', str(self.root))[0], 0)

    def test_bad(self):
        self.put('README.md', 'carte grise extraction')
        code, output = self.cli('audit', str(self.root), '--json')
        self.assertEqual(code, 2)
        result = json.loads(output)
        self.assertEqual(result['verdict'], 'FAIL')
        self.assertEqual(result['findings'][0]['rule'], 'documented-carte-grise-extraction-claim-false')
        self.assertEqual(result['findings'][0]['severity'], 'HIGH')
        self.assertTrue(result['findings'][0]['message'])

    def test_denial(self):
        self.put('README.md', 'does not extract carte grises')
        self.assertEqual(self.cli('audit', str(self.root))[0], 0)
        self.put('app.py', 'x.extract_carte_grise()')
        result = audit(self.root)
        self.assertEqual(result['findings'][0]['rule'], 'documented-no-carte-grise-extraction-claim-false')
        self.assertEqual(result['findings'][0]['severity'], 'HIGH')
        self.assertEqual(self.cli('audit', str(self.root))[0], 2)

    def test_test_only(self):
        self.put('README.md', 'carte grise extraction')
        self.put('tests/test_example.py', 'x.extract_carte_grise()')
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'MEDIUM')
        self.assertEqual(self.cli('audit', str(self.root))[0], 0)
        self.assertEqual(self.cli('audit', str(self.root), '--fail-on', 'medium')[0], 2)

    def test_no_claim(self):
        self.put('app.py', 'x.extract_carte_grise()')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')

    def test_fences_and_inline(self):
        for marker in ('```', '~~~', '   ````'):
            self.put('README.md', marker+'text\ncarte grise extraction\n'+marker.strip())
            self.assertEqual(audit(self.root)['findings'], [])
        self.put('README.md', '`carte grise extraction`')
        self.assertEqual(len(audit(self.root)['findings']), 1)

    def test_docs_and_paragraphs(self):
        self.put('other.md', 'carte grise extraction')
        self.assertFalse(audit(self.root)['findings'])
        self.put('docs/nested/page.md', "doesn't extract carte-grises")
        self.assertFalse(audit(self.root)['findings'])
        self.put('docs/nested/page.md', 'carte grise\n\nextraction')
        self.assertFalse(audit(self.root)['findings'])
        self.put('docs/nested/page.md', 'CARTE-GRISE\nEXTRACTION')
        self.assertTrue(audit(self.root)['findings'])

    def test_single_module(self):
        self.put('README.md', 'carte grise extraction')
        self.put('one.py', 'import mindee\nc = mindee.Client()')
        self.put('two.py', 'import mindee\nc.parse(product.CarteGriseV1)')
        self.assertTrue(audit(self.root)['findings'])

    def test_exclusions(self):
        for name in ('fixtures/a.py', 'docs/a.py', 'examples/a.py'):
            self.put(name, 'x.extract_carte_grise()')
        self.assertFalse(audit(self.root)['production_evidence'])
        for name in ('tests/a.py', 'test_a.py', 'a_test.py'):
            self.put(name, 'x.extract_carte_grise()')
        self.assertEqual(len(audit(self.root)['test_evidence']), 3)

    def test_symlinks_and_ignore(self):
        self.put('real/a.py', 'x.extract_carte_grise()')
        (self.root/'link.py').symlink_to(self.root/'real/a.py')
        (self.root/'linked').symlink_to(self.root/'real', target_is_directory=True)
        self.assertEqual(len(audit(self.root)['production_evidence']), 1)
        self.assertFalse(audit(self.root, ignore=['real'])['production_evidence'])
        self.put('really/a.py', 'x.extract_carte_grise()')
        self.assertEqual(len(audit(self.root, ignore=['real'])['production_evidence']), 1)

    def test_usage(self):
        for args in ([], ['bad'], ['audit', '/nonexistent/r204'], ['audit', str(self.root), '--fail-on', 'MEDIUM'], ['audit', str(self.root), '--ignore', 'a', 'b']):
            self.assertEqual(self.cli(*args)[0], 1)
        self.assertEqual(self.cli('--version'), (0, '0.1.0\n'))
        self.assertEqual(self.cli('audit', str(self.root), '--verbose')[0], 0)

    def test_both_entry_points(self):
        import subprocess
        import sys
        result = subprocess.run([sys.executable, '-m', 'carte_grise_extraction_claim_audit', '--version'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '0.1.0\n')

    def test_self_readme(self):
        readme = Path(__file__).resolve().parents[1] / 'README.md'
        for line, paragraph in __import__('carte_grise_extraction_claim_audit.audit', fromlist=['paragraphs']).paragraphs(readme.read_text()):
            self.assertEqual(claims(paragraph), ([], []), str(line))


def route_test(source, expected):
    def test(self):
        evidence = module_evidence(source)
        self.assertEqual(bool(evidence), expected, source)
    return test

setattr(AuditTests, "test_route_generic_attribute_extract_carte_grise", route_test('x.extract_carte_grise()', True))
setattr(AuditTests, "test_route_generic_import_extract_carte_grise", route_test('from vendor import extract_carte_grise as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_extract_carte_grises", route_test('x.extract_carte_grises()', True))
setattr(AuditTests, "test_route_generic_import_extract_carte_grises", route_test('from vendor import extract_carte_grises as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_parse_carte_grise", route_test('x.parse_carte_grise()', True))
setattr(AuditTests, "test_route_generic_import_parse_carte_grise", route_test('from vendor import parse_carte_grise as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_parse_carte_grises", route_test('x.parse_carte_grises()', True))
setattr(AuditTests, "test_route_generic_import_parse_carte_grises", route_test('from vendor import parse_carte_grises as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_extract_vehicle_registration_certificate", route_test('x.extract_vehicle_registration_certificate()', True))
setattr(AuditTests, "test_route_generic_import_extract_vehicle_registration_certificate", route_test('from vendor import extract_vehicle_registration_certificate as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_parse_vehicle_registration_certificate", route_test('x.parse_vehicle_registration_certificate()', True))
setattr(AuditTests, "test_route_generic_import_parse_vehicle_registration_certificate", route_test('from vendor import parse_vehicle_registration_certificate as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_extract_registration_certificate", route_test('x.extract_registration_certificate()', True))
setattr(AuditTests, "test_route_generic_import_extract_registration_certificate", route_test('from vendor import extract_registration_certificate as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_parse_registration_certificate", route_test('x.parse_registration_certificate()', True))
setattr(AuditTests, "test_route_generic_import_parse_registration_certificate", route_test('from vendor import parse_registration_certificate as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_extract_carte_grise_data", route_test('x.extract_carte_grise_data()', True))
setattr(AuditTests, "test_route_generic_import_extract_carte_grise_data", route_test('from vendor import extract_carte_grise_data as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_parse_carte_grise_data", route_test('x.parse_carte_grise_data()', True))
setattr(AuditTests, "test_route_generic_import_parse_carte_grise_data", route_test('from vendor import parse_carte_grise_data as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_carte_grise_extraction", route_test('x.carte_grise_extraction()', True))
setattr(AuditTests, "test_route_generic_import_carte_grise_extraction", route_test('from vendor import carte_grise_extraction as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_carte_grise_extractor", route_test('x.carte_grise_extractor()', True))
setattr(AuditTests, "test_route_generic_import_carte_grise_extractor", route_test('from vendor import carte_grise_extractor as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_carte_grise_parser", route_test('x.carte_grise_parser()', True))
setattr(AuditTests, "test_route_generic_import_carte_grise_parser", route_test('from vendor import carte_grise_parser as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_vehicle_registration_certificate_extraction", route_test('x.vehicle_registration_certificate_extraction()', True))
setattr(AuditTests, "test_route_generic_import_vehicle_registration_certificate_extraction", route_test('from vendor import vehicle_registration_certificate_extraction as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_vehicle_registration_certificate_extractor", route_test('x.vehicle_registration_certificate_extractor()', True))
setattr(AuditTests, "test_route_generic_import_vehicle_registration_certificate_extractor", route_test('from vendor import vehicle_registration_certificate_extractor as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_vehicle_registration_certificate_parser", route_test('x.vehicle_registration_certificate_parser()', True))
setattr(AuditTests, "test_route_generic_import_vehicle_registration_certificate_parser", route_test('from vendor import vehicle_registration_certificate_parser as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_extract_carte_grise_info", route_test('x.extract_carte_grise_info()', True))
setattr(AuditTests, "test_route_generic_import_extract_carte_grise_info", route_test('from vendor import extract_carte_grise_info as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_parse_carte_grise_info", route_test('x.parse_carte_grise_info()', True))
setattr(AuditTests, "test_route_generic_import_parse_carte_grise_info", route_test('from vendor import parse_carte_grise_info as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_carte_grise_scan", route_test('x.carte_grise_scan()', True))
setattr(AuditTests, "test_route_generic_import_carte_grise_scan", route_test('from vendor import carte_grise_scan as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_carte_grise_scanner", route_test('x.carte_grise_scanner()', True))
setattr(AuditTests, "test_route_generic_import_carte_grise_scanner", route_test('from vendor import carte_grise_scanner as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_scan_carte_grise", route_test('x.scan_carte_grise()', True))
setattr(AuditTests, "test_route_generic_import_scan_carte_grise", route_test('from vendor import scan_carte_grise as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_scan_carte_grises", route_test('x.scan_carte_grises()', True))
setattr(AuditTests, "test_route_generic_import_scan_carte_grises", route_test('from vendor import scan_carte_grises as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_extract_registration_certificate_data", route_test('x.extract_registration_certificate_data()', True))
setattr(AuditTests, "test_route_generic_import_extract_registration_certificate_data", route_test('from vendor import extract_registration_certificate_data as run\nrun()', True))
setattr(AuditTests, "test_route_generic_attribute_parse_registration_certificate_data", route_test('x.parse_registration_certificate_data()', True))
setattr(AuditTests, "test_route_generic_import_parse_registration_certificate_data", route_test('from vendor import parse_registration_certificate_data as run\nrun()', True))
setattr(AuditTests, "test_route_mindee_product_0", route_test('import mindee\nfrom mindee.product.fr import CarteGriseV1\nc=mindee.Client()\nc.parse(product.CarteGriseV1)', True))
setattr(AuditTests, "test_route_mindee_product_1", route_test('import mindee\nfrom mindee.product.fr import CarteGriseV1\nc=mindee.Client()\nc.parse(CarteGriseV1)', True))
setattr(AuditTests, "test_route_mindee_product_2", route_test('import mindee\nfrom mindee.product.fr import CarteGriseV1\nc=mindee.Client()\nc.parse(mindee.product.fr.CarteGriseV1)', True))
setattr(AuditTests, "test_route_mindee_product_3", route_test('import mindee\nfrom mindee.product.fr import CarteGriseV1\nc=mindee.Client()\nc.parse(mindee.v1.product.fr.CarteGriseV1)', True))
setattr(AuditTests, "test_route_mindee_alias", route_test('import mindee as m\nc=m.Client()\nc.parse(product.CarteGriseV1)', True))
setattr(AuditTests, "test_route_mindee_from_alias", route_test('from mindee import Client as C\nc=C()\nc.parse(product_class=product.CarteGriseV1)', True))
setattr(AuditTests, "test_route_mindee_dead", route_test('import mindee\nif False:\n c=mindee.Client()\n c.parse(CarteGriseV1)', True))
setattr(AuditTests, "test_not_evidence_import_mindee", route_test('import mindee', False))
setattr(AuditTests, "test_not_evidence_import_veryfi", route_test('import veryfi', False))
setattr(AuditTests, "test_not_evidence_import_azure_ai_formrecognizer", route_test('import azure.ai.formrecognizer', False))
setattr(AuditTests, "test_not_evidence_import_azure_ai_documentintelligence", route_test('import azure.ai.documentintelligence', False))
setattr(AuditTests, "test_not_evidence_import_google_cloud_documentai", route_test('import google.cloud.documentai', False))
setattr(AuditTests, "test_not_evidence_import_carsxe", route_test('import carsxe', False))
setattr(AuditTests, "test_not_evidence_import_boto3", route_test('import boto3', False))
setattr(AuditTests, "test_not_evidence_mindee_other_InvoiceV4", route_test('import mindee\nc=mindee.Client()\nc.parse(product.InvoiceV4)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_ReceiptV5", route_test('import mindee\nc=mindee.Client()\nc.parse(product.ReceiptV5)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_PassportV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.PassportV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_FinancialDocumentV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.FinancialDocumentV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_BankCheckV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.BankCheckV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_BankAccountDetailsV2", route_test('import mindee\nc=mindee.Client()\nc.parse(product.BankAccountDetailsV2)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_PayslipV2", route_test('import mindee\nc=mindee.Client()\nc.parse(product.PayslipV2)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_PayslipV3", route_test('import mindee\nc=mindee.Client()\nc.parse(product.PayslipV3)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_HealthcareCardV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.HealthcareCardV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_BusinessCardV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.BusinessCardV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_CustomV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.CustomV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_GeneratedV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.GeneratedV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_BillOfLadingV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.BillOfLadingV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_ResumeV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.ResumeV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_DeliveryNoteV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.DeliveryNoteV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_DriverLicenseV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.DriverLicenseV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_IdCardV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.IdCardV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_InternationalIdV2", route_test('import mindee\nc=mindee.Client()\nc.parse(product.InternationalIdV2)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_EnergyBillV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.EnergyBillV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_other_TypeCarteGriseV1", route_test('import mindee\nc=mindee.Client()\nc.parse(product.TypeCarteGriseV1)', False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_invoice", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-invoice')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_receipt", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-receipt')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_layout", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-layout')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_read", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-read')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_idDocument", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-idDocument')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_check_us", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-check.us')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_tax_us", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-tax.us')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_bankStatement_us", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-bankStatement.us')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_payStub_us", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-payStub.us')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_healthInsuranceCard_us", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-healthInsuranceCard.us')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_businessCard", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-businessCard')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_creditCard", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-creditCard')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_contract", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-contract')", False))
setattr(AuditTests, "test_not_evidence_azure_prebuilt_mortgage_us_1003", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('prebuilt-mortgage.us.1003')", False))
setattr(AuditTests, "test_not_evidence_azure_anything", route_test("import azure.ai.documentintelligence\nc.begin_analyze_document('anything')", False))
setattr(AuditTests, "test_not_evidence_veryfi_process_any_document", route_test('import veryfi\nc=veryfi.Client()\nc.process_any_document("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_any_document_url", route_test('import veryfi\nc=veryfi.Client()\nc.process_any_document_url("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_document", route_test('import veryfi\nc=veryfi.Client()\nc.process_document("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_document_url", route_test('import veryfi\nc=veryfi.Client()\nc.process_document_url("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_w2_document", route_test('import veryfi\nc=veryfi.Client()\nc.process_w2_document("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_w9_document", route_test('import veryfi\nc=veryfi.Client()\nc.process_w9_document("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_w8_document", route_test('import veryfi\nc=veryfi.Client()\nc.process_w8_document("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_check", route_test('import veryfi\nc=veryfi.Client()\nc.process_check("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_check_url", route_test('import veryfi\nc=veryfi.Client()\nc.process_check_url("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_check_with_remittance", route_test('import veryfi\nc=veryfi.Client()\nc.process_check_with_remittance("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_check_with_remittance_url", route_test('import veryfi\nc=veryfi.Client()\nc.process_check_with_remittance_url("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_bank_statement_document", route_test('import veryfi\nc=veryfi.Client()\nc.process_bank_statement_document("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_bank_statement_document_url", route_test('import veryfi\nc=veryfi.Client()\nc.process_bank_statement_document_url("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_bussines_card_document", route_test('import veryfi\nc=veryfi.Client()\nc.process_bussines_card_document("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_bussines_card_document_url", route_test('import veryfi\nc=veryfi.Client()\nc.process_bussines_card_document_url("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_classify_document", route_test('import veryfi\nc=veryfi.Client()\nc.classify_document("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_get_business_cards", route_test('import veryfi\nc=veryfi.Client()\nc.get_business_cards("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_get_business_card", route_test('import veryfi\nc=veryfi.Client()\nc.get_business_card("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_delete_business_card", route_test('import veryfi\nc=veryfi.Client()\nc.delete_business_card("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_carte_grise_document", route_test('import veryfi\nc=veryfi.Client()\nc.process_carte_grise_document("file")', False))
setattr(AuditTests, "test_not_evidence_veryfi_process_carte_grise_document_url", route_test('import veryfi\nc=veryfi.Client()\nc.process_carte_grise_document_url("file")', False))
setattr(AuditTests, "test_not_evidence_textract_analyze_document", route_test('import boto3\nc=boto3.client("textract")\nc.analyze_document()', False))
setattr(AuditTests, "test_not_evidence_textract_analyze_expense", route_test('import boto3\nc=boto3.client("textract")\nc.analyze_expense()', False))
setattr(AuditTests, "test_not_evidence_textract_analyze_id", route_test('import boto3\nc=boto3.client("textract")\nc.analyze_id()', False))
setattr(AuditTests, "test_not_evidence_textract_start_document_analysis", route_test('import boto3\nc=boto3.client("textract")\nc.start_document_analysis()', False))
setattr(AuditTests, "test_not_evidence_textract_get_expense_analysis", route_test('import boto3\nc=boto3.client("textract")\nc.get_expense_analysis()', False))
setattr(AuditTests, "test_not_evidence_carsxe_vin_ocr", route_test('import carsxe\nc.vin_ocr()', False))
setattr(AuditTests, "test_not_evidence_carsxe_plate_image_recognition", route_test('import carsxe\nc.plate_image_recognition()', False))
setattr(AuditTests, "test_not_evidence_carsxe_plate_decoder", route_test('import carsxe\nc.plate_decoder()', False))
setattr(AuditTests, "test_not_evidence_carsxe_specs", route_test('import carsxe\nc.specs()', False))
setattr(AuditTests, "test_not_evidence_mindee_client", route_test('import mindee\nmindee.Client()', False))
setattr(AuditTests, "test_not_evidence_mindee_parse_only", route_test('import mindee\nc.parse(CarteGriseV1)', False))
setattr(AuditTests, "test_not_evidence_no_import", route_test('c=mindee.Client()\nc.parse(CarteGriseV1)', False))
setattr(AuditTests, "test_not_evidence_azure_client", route_test('from azure.ai.documentintelligence import DocumentIntelligenceClient\nDocumentIntelligenceClient()', False))
setattr(AuditTests, "test_not_evidence_veryfi_client", route_test('import veryfi\nveryfi.Client()', False))
setattr(AuditTests, "test_not_evidence_google_process", route_test('from google.cloud import documentai\nc.process_document()', False))
setattr(AuditTests, "test_not_evidence_google_batch", route_test('from google.cloud import documentai\nc.batch_process_documents()', False))
setattr(AuditTests, "test_not_evidence_eden_invoice", route_test('c.universal_ai(model="ocr/invoice_parser/affinda")', False))
setattr(AuditTests, "test_not_evidence_eden_resume", route_test('c.universal_ai(model="ocr/resume_parser/affinda")', False))
setattr(AuditTests, "test_not_evidence_llamaparse", route_test('from llama_parse import LlamaParse\nLlamaParse().load_data("file")', False))
setattr(AuditTests, "test_not_evidence_raw_veryfi", route_test('requests.post("https://api.veryfi.com/api/v8/partner/documents")', False))
setattr(AuditTests, "test_not_evidence_pdfplumber", route_test('p.extract_text()', False))
setattr(AuditTests, "test_not_evidence_ocr", route_test('pytesseract.image_to_string(image)', False))
setattr(AuditTests, "test_not_evidence_pandas", route_test('pandas.read_csv("file")', False))
setattr(AuditTests, "test_not_evidence_excel", route_test('pandas.read_excel("file")', False))
setattr(AuditTests, "test_not_evidence_camelot", route_test('camelot.read_pdf("file")', False))
setattr(AuditTests, "test_not_evidence_tabula", route_test('tabula.read_pdf("file")', False))
setattr(AuditTests, "test_not_evidence_convert", route_test('tabula.convert_into("file")', False))
setattr(AuditTests, "test_not_evidence_table", route_test('page.extract_table()', False))
setattr(AuditTests, "test_not_evidence_regex", route_test('import re\nplate=re.search("plate", text)\nfields={"plate":plate}', False))
setattr(AuditTests, "test_not_evidence_string_parse", route_test('text.split("carte grise")', False))
setattr(AuditTests, "test_not_evidence_subprocess_mindee", route_test('import subprocess\nsubprocess.run(["mindee", "parse", "carte_grise"])', False))
setattr(AuditTests, "test_not_evidence_subprocess_veryfi", route_test('import subprocess\nsubprocess.run(["veryfi", "file"])', False))
setattr(AuditTests, "test_not_evidence_bare_name", route_test('extract_carte_grise()', False))
setattr(AuditTests, "test_not_evidence_reference", route_test('x.extract_carte_grise', False))
setattr(AuditTests, "test_not_evidence_string", route_test('"x.extract_carte_grise()"', False))
setattr(AuditTests, "test_not_evidence_comment", route_test('# x.extract_carte_grise()', False))
setattr(AuditTests, "test_not_evidence_invalid", route_test('x.extract_carte_grise(]', False))
setattr(AuditTests, "test_not_evidence_shadow_function", route_test('from v import extract_carte_grise\ndef extract_carte_grise(): pass\nextract_carte_grise()', False))
setattr(AuditTests, "test_not_evidence_shadow_method", route_test('class C:\n def extract_carte_grise(self): pass\nx.extract_carte_grise()', False))
setattr(AuditTests, "test_not_evidence_shadow_class", route_test('from v import extract_carte_grise\nclass extract_carte_grise: pass\nextract_carte_grise()', False))
setattr(AuditTests, "test_not_evidence_shadow_assign", route_test('from v import extract_carte_grise as run\nrun=other\nrun()', False))
setattr(AuditTests, "test_not_evidence_shadow_annotated", route_test('from v import extract_carte_grise as run\nrun: object=other\nrun()', False))
setattr(AuditTests, "test_not_evidence_shadow_with", route_test('from v import extract_carte_grise as run\nwith context() as run:\n run()', False))
setattr(AuditTests, "test_not_evidence_shadow_async_with", route_test('from v import extract_carte_grise as run\nasync def f():\n async with context() as run:\n  run()', False))
setattr(AuditTests, "test_not_evidence_shadow_client", route_test('from mindee import Client\nClient=other\nClient()\nc.parse(CarteGriseV1)', False))
setattr(AuditTests, "test_not_evidence_shadow_module", route_test('import mindee\nwith context() as mindee:\n c=mindee.Client()\n c.parse(CarteGriseV1)', False))
setattr(AuditTests, "test_not_evidence_shadow_parse", route_test('import mindee\ndef parse(): pass\nc=mindee.Client()\nc.parse(CarteGriseV1)', False))
setattr(AuditTests, "test_not_evidence_shadow_product", route_test('import mindee\nclass CarteGriseV1: pass\nc=mindee.Client()\nc.parse(CarteGriseV1)', False))
setattr(AuditTests, "test_not_evidence_mindee_v2", route_test('import mindee\nc.enqueue_and_parse(model_id="opaque")', False))
setattr(AuditTests, "test_not_evidence_docupipe", route_test('import docupipe\nc.upload("opaque-id")', False))
setattr(AuditTests, "test_not_evidence_konfuzio", route_test('import konfuzio\nc.upload("opaque-id")', False))
setattr(AuditTests, "test_not_evidence_rpacpc", route_test('import rpacpc\nc.upload("opaque-id")', False))
setattr(AuditTests, "test_not_evidence_wintone", route_test('import wintone\nc.upload("opaque-id")', False))
setattr(AuditTests, "test_not_evidence_nanonets", route_test('import nanonets\nc.upload("opaque-id")', False))
setattr(AuditTests, "test_not_evidence_docsumo", route_test('import docsumo\nc.upload("opaque-id")', False))
setattr(AuditTests, "test_not_evidence_abbyy", route_test('import abbyy\nc.upload("opaque-id")', False))
setattr(AuditTests, "test_not_evidence_rossum", route_test('import rossum\nc.upload("opaque-id")', False))
setattr(AuditTests, "test_not_evidence_klippa", route_test('import klippa\nc.upload("opaque-id")', False))
setattr(AuditTests, "test_not_evidence_parseur", route_test('import parseur\nc.upload("opaque-id")', False))
setattr(AuditTests, "test_not_evidence_extend", route_test('import extend\nc.upload("opaque-id")', False))
setattr(AuditTests, "test_not_evidence_extract_tables", route_test('page.extract_tables()', False))
setattr(AuditTests, "test_not_evidence_find_table", route_test('page.find_table()', False))
setattr(AuditTests, "test_not_evidence_find_tables", route_test('page.find_tables()', False))

if __name__ == "__main__":
    unittest.main()
