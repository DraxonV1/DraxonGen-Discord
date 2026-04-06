from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README if present
here = Path(__file__).parent
long_description = (here / "README.md").read_text(encoding="utf-8") if (here / "README.md").exists() else ""

# â”€â”€ Nuitka compilation metadata (embedded into the compiled .exe) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# When building with Nuitka use:
#   python -m nuitka --onefile --product-name="MuskDTA Launcher"
#                    --product-version=1.0.0
#                    --file-description="MuskServices DTA Launcher"
#                    --company-name="DraxonV1 / MuskServices"
#                    --copyright="Copyright (c) 2025 DraxonV1"
#                    --windows-icon-from-ico=icon.ico   (optional)
#                    muskdta/cli.py
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

setup(
    # â”€â”€ Identity â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    name="muskdta",
    version="1.0.1",
    author="DraxonV1",
    author_email="",
    description="MuskServices DTA â€” Python launcher, updater & config manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DraxonV1/MuskServices-DTA",
    project_urls={
        "Discord": "https://discord.gg/dpk45Be2e3",
        "Source":  "https://github.com/DraxonV1/MuskServices-DTA",
    },

    # â”€â”€ Nuitka metadata (picked up at compile time) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    options={
        "nuitka": {
            "product-name":    "MuskDTA Launcher",
            "product-version": "1.0.0",
            "file-description":"MuskServices DTA Launcher",
            "company-name":    "DraxonV1 / MuskServices",
            "copyright":       "Copyright (c) 2025 DraxonV1",
        }
    },

    # â”€â”€ Package contents â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    packages=find_packages(),
    python_requires=">=3.9",

    install_requires=[
        "requests>=2.28.0",
        "easygradients>=0.1.2",
    ],

    entry_points={
        "console_scripts": [
            "muskdta=muskdta.cli:main",
        ]
    },

    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
    ],
)
