# /tmp/nl_erpnext_rgs_mkb/setup.py
from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="nl_erpnext_rgs_mkb",
    version="0.1.0",
    description="Dutch RGS MKB 3.7 compliance for ERPNext",
    author="Your Organization",
    author_email="admin@fivi.eu",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)