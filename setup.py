import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="docdecay",
    version="0.2.8",
    description="Monitor documentation for staleness",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/kshehadeh/decay",
    author="Karim Shehadeh",
    author_email="kshehadeh@underarmour.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["decay","decay.markers","decay.analyzers"],
    include_package_data=True,
    install_requires=[
        "python-frontmatter",
        "sendgrid",
        "PyGithub",
        "markdown2",
        "email_validator",
        "configargparse",
        "pyfluence",
        "arrow"
    ],
    entry_points={
        "console_scripts": [
            "decay=decay.main:main",
        ]
    },
)
