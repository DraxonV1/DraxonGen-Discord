from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README if present
here = Path(__file__).parent
readme = here / "README.md"
long_description = readme.read_text(encoding="utf-8") if readme.exists() else ""

setup(
    # Identity
    name="muskdta",
    version="0.0.0",
    author="DraxonV1",
    author_email="",
    description="MuskServices DTA - Python launcher, updater & config manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DraxonV1/MuskServices-DTA",
    project_urls={
        "Discord": "https://discord.gg/dpk45Be2e3",
        "Source": "https://github.com/DraxonV1/MuskServices-DTA",
    },

    # Package contents
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