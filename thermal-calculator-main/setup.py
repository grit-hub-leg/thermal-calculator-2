# setup.py

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="data-center-cooling-calculator",
    version="1.0.0",
    author="Your Organization",
    author_email="contact@example.com",
    description="A comprehensive calculator for data center cooling solutions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-organization/data-center-cooling-calculator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=[
        "flask>=2.0.0",
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "matplotlib>=3.4.0",
        "pyyaml>=6.0",
        "requests>=2.26.0",
        "pypdf>=3.0.0",
        "reportlab>=3.6.0",
        "pytest>=6.2.5",
    ],
    entry_points={
        "console_scripts": [
            "cooling-calculator=main:main",
            "cooling-api=api.app:main",
            "cooling-web=ui.web.app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.html", "*.css", "*.js"],
    },
)
