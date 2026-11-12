""" Run the neutral lint of ``backend_neutral_tests/lint_neutral.py``. """
import importlib.util
from pathlib import Path

#: root of the repository: <root>/odoo/addons/test_backend_neutral/harness/lint.py
REPOSITORY_ROOT = Path(__file__).parents[4]
LINT_SCRIPT = REPOSITORY_ROOT / 'backend_neutral_tests' / 'lint_neutral.py'


def load_lint():
    """ Return the lint module; it is not importable by name on purpose. """
    spec = importlib.util.spec_from_file_location('backend_neutral_lint', LINT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lint_findings(*paths) -> list[str]:
    """ Return the findings of the neutral lint on the given files and
    directories, as ``path:line: BNxxx message``. """
    lint = load_lint()
    return [
        f"{path}:{line}: {code} {message}"
        for path in lint.iter_files([str(path) for path in paths])
        for line, code, message in lint.lint_source(path.read_text(encoding='utf-8'), str(path))
    ]
