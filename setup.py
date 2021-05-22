from setuptools import setup, find_packages

setup(
    name="h3pandas",
    version=0.1,
    license="MIT",
    description="Integration of H3 and GeoPandas",
    author="Dahn",
    author_email="dahnjahn@gmail.com",
    url="https://github.com/DahnJ/H3-Pandas",
    download_url="TODO",
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
    install_requires=[],
    python_requires=">=3.7"
)
