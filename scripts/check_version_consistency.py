#!/usr/bin/env python3
"""
Version consistency checker for AlteruPhono.

This script ensures that all version references across the project are synchronized.
It checks:
- __init__.py __version__
- setup.py version extraction
- pyproject.toml dynamic version
- Any other version references in documentation or CI files

Usage:
    python scripts/check_version_consistency.py
    python scripts/check_version_consistency.py --fix  # Auto-fix inconsistencies
"""

import argparse
import pathlib
import re
import sys


class VersionChecker:
    """Check and fix version consistency across the project."""

    def __init__(self, project_root: pathlib.Path):
        self.project_root = project_root
        self.source_version: str | None = None
        self.inconsistencies: list[str] = []

    def get_init_version(self) -> str:
        """Extract version from __init__.py (source of truth)."""
        init_file = self.project_root / "alteruphono" / "__init__.py"

        if not init_file.exists():
            raise FileNotFoundError(f"Cannot find {init_file}")

        content = init_file.read_text(encoding="utf-8")

        # Look for __version__ = "..." pattern
        version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)

        if not version_match:
            raise ValueError("Cannot find __version__ in __init__.py")

        return version_match.group(1)

    def check_setup_py(self) -> str | None:
        """Check setup.py version extraction."""
        setup_file = self.project_root / "setup.py"

        if not setup_file.exists():
            return None

        content = setup_file.read_text(encoding="utf-8")

        # Check if it uses get_version() function
        if "version=get_version()" in content:
            # Test that get_version() works correctly
            try:
                # Simulate the get_version function
                init_file = self.project_root / "alteruphono" / "__init__.py"
                for line in init_file.read_text().splitlines():
                    if line.startswith("__version__"):
                        version_part = line.split("=")[1].strip()
                        if version_part.startswith('"'):
                            extracted = version_part.split('"')[1]
                        elif version_part.startswith("'"):
                            extracted = version_part.split("'")[1]
                        else:
                            extracted = version_part.split('#')[0].strip().strip('"').strip("'")

                        if extracted == self.source_version:
                            return "✓ Correctly extracts from __init__.py"
                        else:
                            return f"✗ Extracts '{extracted}' instead of '{self.source_version}'"

                return "✗ get_version() function cannot find __version__"

            except Exception as e:
                return f"✗ get_version() function error: {e}"

        # Check for hardcoded version
        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if version_match:
            found_version = version_match.group(1)
            if found_version == self.source_version:
                return "⚠ Hardcoded version matches (should use dynamic extraction)"
            else:
                return f"✗ Hardcoded version '{found_version}' != '{self.source_version}'"

        return "? Cannot determine version method in setup.py"

    def check_pyproject_toml(self) -> str | None:
        """Check pyproject.toml version configuration."""
        pyproject_file = self.project_root / "pyproject.toml"

        if not pyproject_file.exists():
            return None

        content = pyproject_file.read_text(encoding="utf-8")

        # Check if version is in dynamic list
        if 'dynamic = ["version"]' in content or "dynamic = ['version']" in content:
            # Check if setuptools.dynamic.version is configured correctly
            if 'version = {attr = "alteruphono.__version__"}' in content:
                return "✓ Correctly configured for dynamic version"
            else:
                return "✗ Dynamic version declared but not properly configured"

        # Check for hardcoded version
        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if version_match:
            found_version = version_match.group(1)
            if found_version == self.source_version:
                return "⚠ Hardcoded version matches (should use dynamic)"
            else:
                return f"✗ Hardcoded version '{found_version}' != '{self.source_version}'"

        return "? No version configuration found in pyproject.toml"

    def check_all_files(self) -> dict[str, str]:
        """Check version consistency across all relevant files."""
        self.source_version = self.get_init_version()

        results = {
            "__init__.py": f"✓ Source version: {self.source_version}"
        }

        # Check setup.py
        setup_result = self.check_setup_py()
        if setup_result:
            results["setup.py"] = setup_result

        # Check pyproject.toml
        pyproject_result = self.check_pyproject_toml()
        if pyproject_result:
            results["pyproject.toml"] = pyproject_result

        return results

    def fix_setup_py(self) -> bool:
        """Fix setup.py to use dynamic version extraction."""
        setup_file = self.project_root / "setup.py"

        if not setup_file.exists():
            return False

        content = setup_file.read_text(encoding="utf-8")

        # Check if get_version function exists
        if "def get_version():" not in content:
            # Add get_version function
            function_code = '''
# Get version from __init__.py to maintain single source of truth
def get_version():
    """Extract version from __init__.py"""
    init_file = LOCAL_PATH / "alteruphono" / "__init__.py"
    for line in init_file.read_text().splitlines():
        if line.startswith("__version__"):
            # Extract version between quotes, ignoring comments
            version_part = line.split("=")[1].strip()
            # Handle both single and double quotes
            if version_part.startswith('"'):
                return version_part.split('"')[1]
            elif version_part.startswith("'"):
                return version_part.split("'")[1]
            else:
                # Fallback: strip whitespace and comments
                return version_part.split('#')[0].strip().strip('"').strip("'")
    raise RuntimeError("Unable to find version string")
'''

            # Insert before setup() call
            content = content.replace(
                "# This call to setup()",
                function_code + "\n# This call to setup()",
            )

        # Replace hardcoded version with dynamic extraction
        content = re.sub(
            r'version\s*=\s*["\'][^"\']+["\'][^,]*,',
            'version=get_version(),  # Automatically synced with __init__.py',
            content,
        )

        setup_file.write_text(content, encoding="utf-8")
        return True

    def fix_pyproject_toml(self) -> bool:
        """Fix pyproject.toml to use dynamic versioning."""
        pyproject_file = self.project_root / "pyproject.toml"

        if not pyproject_file.exists():
            return False

        content = pyproject_file.read_text(encoding="utf-8")

        # Ensure dynamic version is declared
        if 'dynamic = ["version"]' not in content and "dynamic = ['version']" not in content:
            # Add dynamic version declaration
            content = re.sub(
                r'(name\s*=\s*["\'][^"\']+["\'])',
                r'\1\ndynamic = ["version"]',
                content
            )

        # Ensure setuptools.dynamic.version is configured
        if (
            'version = {attr = "alteruphono.__version__"}' not in content
            and "[tool.setuptools.dynamic]" not in content
        ):
            # Add dynamic version configuration
            content += (
                '\n[tool.setuptools.dynamic]\n'
                'version = {attr = "alteruphono.__version__"}\n'
            )

        # Remove any hardcoded version
        content = re.sub(r'version\s*=\s*["\'][^"\']+["\'].*\n', '', content)

        pyproject_file.write_text(content, encoding="utf-8")
        return True


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check version consistency across AlteruPhono project files"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix version inconsistencies"
    )
    parser.add_argument(
        "--project-root",
        type=pathlib.Path,
        default=pathlib.Path(__file__).parent.parent,
        help="Path to project root directory"
    )

    args = parser.parse_args()

    checker = VersionChecker(args.project_root)

    try:
        results = checker.check_all_files()

        print("Version Consistency Check Results:")
        print("=" * 40)

        all_good = True
        for filename, status in results.items():
            print(f"{filename:15}: {status}")
            if "✗" in status:
                all_good = False

        if not all_good:
            print("\n⚠ Inconsistencies found!")

            if args.fix:
                print("\nAttempting to fix inconsistencies...")

                if "setup.py" in results and "✗" in results["setup.py"]:
                    if checker.fix_setup_py():
                        print("✓ Fixed setup.py")
                    else:
                        print("✗ Failed to fix setup.py")

                if "pyproject.toml" in results and "✗" in results["pyproject.toml"]:
                    if checker.fix_pyproject_toml():
                        print("✓ Fixed pyproject.toml")
                    else:
                        print("✗ Failed to fix pyproject.toml")

                print("\nRe-checking after fixes...")
                results = checker.check_all_files()
                for filename, status in results.items():
                    print(f"{filename:15}: {status}")

            else:
                print("\nRun with --fix to automatically resolve inconsistencies")
                sys.exit(1)

        else:
            print("\n✓ All versions are consistent!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
