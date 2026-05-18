"""
Cidnilib - Content ID based data manipulation library
"""
from setuptools import setup, find_packages

setup(name="cidnilib",
    version="0.0.1",
    description="Content ID based data manipulation library",
    long_description=__doc__,
    author="Joseph Kendall-Morwick",
    author_email="jbmorwick@gmail.com",
    license = "MIT",
    url="http://github.com/jmorwick/cidni",
    classifiers = [
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Database" ],
    packages=find_packages(),
    install_requires=[
        "pickledb",
        "py-multihash",
        "sniffpy",
    ],
)

