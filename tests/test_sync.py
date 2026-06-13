"""
Sync gate: every public function in am.py is wired up everywhere it must be.

When you add a public function to am.py, this fails immediately if you forget
to: test it, mention it in both READMEs, document it in the GUIDEs, or export
it from the package. Also pins __version__ to pyproject.

Run:  pytest tests/test_sync.py -v
"""
import ast
import pathlib
import re

ROOT = pathlib.Path(__file__).parent.parent

# report() is a print helper, not part of the verifiable surface.
_HELPERS = {"report"}


def _public_funcs() -> list[str]:
    src = (ROOT / "actmirror" / "am.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name.startswith("_") or node.name == "_cli":
            continue
        if node.name in _HELPERS:
            continue
        out.append(node.name)
    return out


FUNCS = _public_funcs()


def test_func_list_nonempty():
    assert len(FUNCS) >= 8, f"Expected ≥8 public functions, found {len(FUNCS)}: {FUNCS}"


# ─────────────────────────────────────────────────────────────
# Gate 1: every public function is tested
# ─────────────────────────────────────────────────────────────
def test_funcs_have_tests():
    test_src = (ROOT / "tests" / "test_am.py").read_text(encoding="utf-8")
    missing = [f for f in FUNCS if f"am.{f}(" not in test_src and f not in test_src]
    assert not missing, "Untested functions:\n" + "\n".join(f"  ✗ {m}" for m in missing)


# ─────────────────────────────────────────────────────────────
# Gate 2: every public function is in both READMEs
# ─────────────────────────────────────────────────────────────
def test_funcs_in_readmes():
    for readme in ("README.md", "README_KO.md"):
        text = (ROOT / readme).read_text(encoding="utf-8")
        missing = [f for f in FUNCS if f not in text]
        assert not missing, f"{readme} missing:\n" + "\n".join(f"  ✗ {m}" for m in missing)


# ─────────────────────────────────────────────────────────────
# Gate 3: every public function is in both GUIDEs
# ─────────────────────────────────────────────────────────────
def test_funcs_in_guides():
    for guide in ("docs/GUIDE.md", "docs/GUIDE_KO.md"):
        text = (ROOT / guide).read_text(encoding="utf-8")
        missing = [f for f in FUNCS if f not in text]
        assert not missing, f"{guide} missing:\n" + "\n".join(f"  ✗ {m}" for m in missing)


# ─────────────────────────────────────────────────────────────
# Gate 4: every public function is exported from the package
# ─────────────────────────────────────────────────────────────
def test_funcs_exported():
    import actmirror
    missing = [f for f in FUNCS if not hasattr(actmirror, f)]
    assert not missing, "Unexported functions:\n" + "\n".join(f"  ✗ {m}" for m in missing)


# ─────────────────────────────────────────────────────────────
# Gate 5: __version__ matches pyproject.toml
# ─────────────────────────────────────────────────────────────
def test_version_matches_pyproject():
    import actmirror
    toml = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', toml, re.MULTILINE)
    assert m, "version not found in pyproject.toml"
    assert actmirror.__version__ == m.group(1), (
        f"Version drift: __init__={actmirror.__version__!r} pyproject={m.group(1)!r}")
