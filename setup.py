import pathlib
import setuptools
from setuptools import setup, find_packages

# The directory containing this file
LOCAL_PATH = pathlib.Path(__file__).parent

# The text of the README file
README_FILE = (LOCAL_PATH / "README.md").read_text()

# Load requirements, so they are listed in a single place
with open("requirements.txt") as fp:
    install_requires = [dep.strip() for dep in fp.readlines()]

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

# This call to setup() does all the work
setup(
    author_email="tiago.tresoldi@lingfil.uu.se",
    author="Tiago Tresoldi",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries",
    ],
    description="Advanced phonological evolution modeling for historical linguistics",
    entry_points={"console_scripts": ["alteruphono=alteruphono.__main__:main"]},
    include_package_data=True,
    install_requires=install_requires,
    keywords=["sound change", "phonology", "historical linguistics", "comparative method", "phonological features", "language evolution"],
    license="MIT",
    long_description_content_type="text/markdown",
    long_description=README_FILE,
    name="alteruphono",
    packages=find_packages() + ["resources"],
    python_requires=">=3.10",
    test_suite="tests",
    tests_require=[],
    url="https://github.com/tresoldi/alteruphono",
    version=get_version(),  # Automatically synced with __init__.py
    zip_safe=False,
)
