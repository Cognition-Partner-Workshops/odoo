""" Run the neutral lint of ``backend_neutral_tests/lint_neutral.py``, on the
addon's tests and on the upstream code its classes inherit. """
import ast
import importlib.util
import inspect
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


# ---------------------------------------------------------------------------
# Lint of the code a neutral class inherits from outside the addon
# ---------------------------------------------------------------------------

#: modules whose classes are not linted: the harness replaces them
_INFRASTRUCTURE_PREFIXES = ('odoo.tests.', 'unittest')


def neutral_test_classes(*modules) -> list[type]:
    """ Return the ``NeutralCase`` subclasses defined in the given modules. """
    from .case import NeutralCase  # noqa: PLC0415
    classes = []
    for module in modules:
        for obj in vars(module).values():
            if isinstance(obj, type) and issubclass(obj, NeutralCase) and obj.__module__ == module.__name__:
                classes.append(obj)
    return classes


def _is_addon_class(cls) -> bool:
    return cls.__module__.startswith(__name__.rsplit('.', 2)[0])


def _is_upstream_class(cls) -> bool:
    return (
        not _is_addon_class(cls)
        and cls.__module__.startswith('odoo.addons.')
        and not cls.__module__.startswith(_INFRASTRUCTURE_PREFIXES)
    )


def _collected_test_names(cls) -> set[str]:
    """ The test methods Odoo's loader collects for ``cls`` (see
    ``odoo/tests/loader.py``): its own ``__dict__`` unless
    ``allow_inherited_tests_method`` is set. """
    if getattr(cls, 'allow_inherited_tests_method', False):
        return {name for name in dir(cls) if name.startswith('test') and callable(getattr(cls, name, None))}
    return {name for name, value in vars(cls).items() if name.startswith('test') and callable(value)}


def lint_inherited(classes) -> tuple[list[str], list[str]]:
    """ Lint the upstream code that the given neutral classes inherit.

    For every base of a class that lives in another addon (``test_base``,
    ``base``), the base's source file is linted and the findings inside the
    base's class body are kept, except those in methods the neutral class
    does not run: methods it overrides (linted in the addon), test methods it
    does not collect, and attributes it sets to ``None``. Returns the kept
    findings and, separately, the findings at module level of the upstream
    files (imports, module helpers), which are reported for review only.
    """
    lint = load_lint()
    files: dict[str, tuple[list, ast.Module]] = {}

    def file_data(path):
        if path not in files:
            source = Path(path).read_text(encoding='utf-8')
            files[path] = (list(lint.lint_source(source, path)), ast.parse(source))
        return files[path]

    findings: list[str] = []
    module_level: list[str] = []
    seen_module_level: set[tuple] = set()
    for cls in classes:
        addon_dicts = [vars(c) for c in cls.__mro__ if _is_addon_class(c)]
        collected = _collected_test_names(cls)
        for base in cls.__mro__:
            if not _is_upstream_class(base):
                continue
            path = inspect.getsourcefile(base)
            file_findings, tree = file_data(path)
            class_node = next(
                (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == base.__name__), None,
            )
            if class_node is None:
                findings.append(f"{path}: class {base.__name__} not found for {cls.__name__}")
                continue
            skipped: list[tuple[int, int, str]] = []
            for node in class_node.body:
                if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                start = min([node.lineno, *(d.lineno for d in node.decorator_list)])
                overridden = any(node.name in d for d in addon_dicts)
                not_run = node.name.startswith('test') and node.name not in collected
                if overridden or not_run:
                    skipped.append((start, node.end_lineno, node.name))
            for line, code, message in file_findings:
                if not class_node.lineno <= line <= class_node.end_lineno:
                    continue
                if any(start <= line <= end for start, end, _name in skipped):
                    continue
                method = next((n for n in class_node.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
                               and min([n.lineno, *(d.lineno for d in n.decorator_list)]) <= line <= n.end_lineno), None)
                where = f"{base.__name__}.{method.name}" if method else base.__name__
                findings.append(f"{path}:{line}: {code} {message} [{where}, inherited by {cls.__name__}]")
            for line, code, message in file_findings:
                in_class = any(isinstance(n, ast.ClassDef) and n.lineno <= line <= n.end_lineno for n in tree.body)
                if not in_class and (path, line, code) not in seen_module_level:
                    seen_module_level.add((path, line, code))
                    module_level.append(f"{path}:{line}: {code} {message} [module level]")
    return findings, module_level
