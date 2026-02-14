from setuptools import setup, find_packages

setup(
    name="bics_sirius_sfrdb_api",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "python-dotenv",
        "pyyaml",
        "oracledb",
    ],
    entry_points={
        "console_scripts": [
            "sfrdb-fetcher = bics_sirius_sfrdb_api.fetcher_main:main",
            "sfrdb-uploader = bics_sirius_sfrdb_api.uploader_main:main",
        ]
    },
)