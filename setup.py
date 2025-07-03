from setuptools import setup, find_packages

setup(
    name="cocotb2_migrator",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "libcst>=1.0.1",
    ],
    python_requires=">=3.7",
)
