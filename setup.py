from setuptools import setup, find_packages

# read the contents of README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="h3pandas",
    version="0.1.1-alpha",
    license="MIT",
    description="Integration of H3 and GeoPandas",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Dahn",
    author_email="dahnjahn@gmail.com",
    url="https://github.com/DahnJ/H3-Pandas",
    download_url="https://github.com/DahnJ/H3-Pandas/archive/refs/tags/0.1.1-alpha.tar.gz",
    keywords=["python", "h3", "geospatial", "geopandas", "pandas", "integration",
              "hexagons-are-awesome"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    packages=find_packages(),
    setup_requires=[],
    install_requires=['geopandas', 'pandas', 'shapely', 'h3', 'numpy'],
    python_requires=">=3.7",
    extras_require={
        'test': ['pytest', 'pytest-cov', 'flake8'],
        'docs': ['sphinx', 'numpydoc', 'pytest-sphinx-theme']
    },
)
