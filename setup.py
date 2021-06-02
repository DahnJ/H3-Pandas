from setuptools import setup, find_packages
from os import path

# read version
with open(path.join('h3pandas', '_version.py')) as f:
    exec(f.read())

# read the contents of README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="h3pandas",
    version=__version__,
    license="MIT",
    description="Integration of H3 and GeoPandas",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Dahn",
    author_email="dahnjahn@gmail.com",
    url="https://github.com/DahnJ/H3-Pandas",
    download_url=f"https://github.com/DahnJ/H3-Pandas/archive/refs/tags/{__version__}.tar.gz",
    keywords=["python", "h3", "geospatial", "geopandas", "pandas", "integration",
              "hexagons-are-bestagons"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    packages=find_packages(),
    setup_requires=[],
    install_requires=['geopandas', 'pandas', 'shapely', 'h3', 'numpy', 'typing-extensions'],
    python_requires=">=3.6",
    extras_require={
        'test': ['pytest', 'pytest-cov', 'flake8'],
        'docs': ['sphinx', 'numpydoc', 'pytest-sphinx-theme', 'typing-extensions']
    },
)
