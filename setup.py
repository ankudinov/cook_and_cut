import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name="ccAVD",
    version="0.1.0",
    description="Cookiecutter for AVD",
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://github.com/ankudinov/cook_and_cut',
    author='Petr Ankudinov',
    license="BSD",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Development Status :: 3 - Alpha",
        "Operating System :: POSIX :: Linux",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "cookiecutter==2.5.0",
    ],
    entry_points = {
        "console_scripts": ['ccAVD = ccAVD.cli:interpreter']
    },
)