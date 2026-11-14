"""Read-only Markdown and AST analysis. Source is never executed."""
import ast
import os
from pathlib import Path
import re

from .phrases import CARTEGRISEEXTRACTION, NOCARTEGRISEEXTRACTION, GENERIC_NAMES


def normalize(text):
    return ' '.join(text.lower().replace("n't", ' not').replace('-', ' ').split())


def pattern(phrases):
    return re.compile(r'\b(?:' + '|'.join(re.escape(p) for p in sorted(phrases, key=lambda p: (-len(p), p))) + r')\b')


POSITIVE = pattern(CARTEGRISEEXTRACTION)
NEGATIVE = pattern(NOCARTEGRISEEXTRACTION)


def claims(text):
    text = normalize(text)
    negative = [m.group() for m in NEGATIVE.finditer(text)]
    text = NEGATIVE.sub(lambda m: ' ' * len(m.group()), text)
    return [m.group() for m in POSITIVE.finditer(text)], negative


def paragraphs(text):
    """Yield prose paragraphs with their starting line, preserving fence rules."""
    fence = None
    block = []
    start = 1
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            continue
        if match:
            if block:
                yield start, '\n'.join(block)
                block = []
            fence = match[1]
            continue
        if not line.strip():
            if block:
                yield start, '\n'.join(block)
                block = []
        else:
            if not block:
                start = number
            block.append(line)
    if block:
        yield start, '\n'.join(block)


def module_evidence(source):
    """Return recognized route locations, with bindings resolved within one module."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    nodes = list(ast.walk(tree))
    imports = {}
    bound = set()
    definitions = {n.name for n in nodes if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    mindee = False

    def bind(target):
        if isinstance(target, ast.Name):
            bound.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                bind(item)
        elif isinstance(target, ast.Starred):
            bind(target.value)

    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.asname or alias.name.split('.')[0]] = alias.name if alias.asname else alias.name.split('.')[0]
                mindee |= alias.name.split('.')[0] == 'mindee'
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            mindee |= module.split('.')[0] == 'mindee'
            for alias in node.names:
                imports[alias.asname or alias.name] = module + '.' + alias.name
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                bind(target)
        elif isinstance(node, ast.AnnAssign):
            bind(node.target)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars:
                    bind(item.optional_vars)

    shadow = bound | definitions

    def resolved(node):
        if isinstance(node, ast.Name):
            return imports.get(node.id, '') if node.id not in shadow else ''
        if isinstance(node, ast.Attribute):
            base = resolved(node.value)
            return base + '.' + node.attr if base else ''
        return ''

    def product(node):
        if isinstance(node, ast.Name):
            return node.id == 'CarteGriseV1' and node.id not in shadow
        return isinstance(node, ast.Attribute) and node.attr == 'CarteGriseV1' and node.attr not in definitions

    clients = []
    parses = []
    result = []
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else (func.id if isinstance(func, ast.Name) else '')
        imported = resolved(func)
        generic = (isinstance(func, ast.Attribute) and name in GENERIC_NAMES and name not in definitions)
        if isinstance(func, ast.Name) and imported:
            generic = imported.rsplit('.', 1)[-1] in GENERIC_NAMES and imported.rsplit('.', 1)[-1] not in definitions
        if generic:
            result.append({'line': node.lineno, 'route': 'generic:' + (name if isinstance(func, ast.Attribute) else imported.rsplit('.', 1)[-1])})
        if mindee and name not in definitions:
            if imported == 'mindee.Client' and 'Client' not in definitions:
                clients.append(node.lineno)
            elif (isinstance(func, ast.Attribute) and func.attr == 'Client' and isinstance(func.value, ast.Name)
                  and func.value.id == 'mindee' and 'mindee' not in shadow):
                clients.append(node.lineno)
            if isinstance(func, ast.Attribute) and name == 'parse' and any(product(arg) for arg in list(node.args) + [kw.value for kw in node.keywords]):
                parses.append(node.lineno)
    if clients and parses:
        result.extend({'line': line, 'route': 'mindee:Client+parse(CarteGriseV1)', 'client_line': min(clients)} for line in parses)
    return sorted(result, key=lambda item: (item['line'], item['route']))


def audit(root, ignore=(), fail_on='high'):
    root = Path(root)
    if not root.is_dir():
        raise OSError('Repository is not a readable directory: ' + str(root))
    prefixes = []
    for prefix in ignore:
        parts = Path(prefix).parts
        if Path(prefix).is_absolute() or '..' in parts:
            raise ValueError('Ignore prefixes must be relative paths without parent traversal')
        prefixes.append(parts)

    def ignored(parts):
        return any(parts[:len(prefix)] == prefix for prefix in prefixes)

    production, tests, positive, negative = [], [], [], []

    def walk_error(error):
        raise error

    for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        base = Path(directory)
        dirs[:] = sorted(d for d in dirs if not (base/d).is_symlink() and not ignored((base/d).relative_to(root).parts))
        for filename in sorted(files):
            path = base / filename
            relative = path.relative_to(root)
            parts = relative.parts
            if path.is_symlink() or ignored(parts):
                continue
            if (relative.as_posix() == 'README.md' or ('docs' in parts[:-1] and path.suffix == '.md')):
                for line, text in paragraphs(path.read_text(encoding='utf-8')):
                    yes, no = claims(text)
                    positive.extend({'path': relative.as_posix(), 'line': line, 'phrase': p} for p in yes)
                    negative.extend({'path': relative.as_posix(), 'line': line, 'phrase': p} for p in no)
            if path.suffix != '.py' or set(parts[:-1]) & {'fixtures', 'docs', 'examples'}:
                continue
            evidence = module_evidence(path.read_text(encoding='utf-8'))
            target = tests if ('tests' in parts[:-1] or filename.startswith('test_') or filename.endswith('_test.py')) else production
            target.extend(dict(item, path=relative.as_posix()) for item in evidence)
    findings = []
    if positive and not production:
        findings.append({'rule': 'documented-carte-grise-extraction-claim-false', 'severity': 'MEDIUM' if tests else 'HIGH',
                         'message': 'Documented capability has only test evidence.' if tests else 'Documented capability has no recognized production evidence.', 'locations': positive})
    if negative and production:
        findings.append({'rule': 'documented-no-carte-grise-extraction-claim-false', 'severity': 'HIGH',
                         'message': 'Documented denial conflicts with recognized production evidence.', 'locations': negative})
    failed = any(f['severity'] == 'HIGH' or fail_on.lower() == 'medium' for f in findings)
    return {'verdict': 'FAIL' if failed else 'PASS', 'findings': findings, 'production_evidence': production, 'test_evidence': tests}
