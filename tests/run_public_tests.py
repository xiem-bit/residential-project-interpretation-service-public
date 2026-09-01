#!/usr/bin/env python3
"""Run every Python test included in the public release candidate."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_FILES = (
    "tools/chinese_copy_lint/test_affirmative_statement_lint.py",
    "tools/product3_chapter2/test_validate_chapter2_contract.py",
    "tools/product3_chapter23/test_validate_chapter23_bridge.py",
    "tools/product3_chapter3/test_validate_chapter3_contract.py",
    "tools/product4/test_validate_product4_contract.py",
    "tests/test_business_gates_public.py",
    "tests/test_inference_firewall.py",
    "tests/test_upstream_exchange.py",
    "tests/test_cross_package_conformance.py",
    "tests/test_product4_xmind_public.py",
    "tests/test_rc1_contracts.py",
    "tests/test_production_path_v02.py",
    "tests/test_capability_parity.py",
    "tests/test_public_release_state.py",
)


def main() -> int:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for index, relative_file in enumerate(TEST_FILES):
        test_file = ROOT / relative_file
        module_name = f"_public_core_test_{index}"
        spec = importlib.util.spec_from_file_location(module_name, test_file)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load test module: {relative_file}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        suite.addTests(loader.loadTestsFromModule(module))

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
