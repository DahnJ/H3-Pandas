<img align="left" src="https://i.imgur.com/OH8DoTA.png" alt="H3 Logo" width="500">


&nbsp;

# H3-Pandas ⬢ 🐼
Integrates [H3](https://github.com/uber/h3-py) with  [GeoPandas](https://github.com/geopandas/geopandas)
and [Pandas](https://github.com/pandas-dev/pandas).

[![image](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DahnJ/H3-Pandas/blob/master/notebook/example.ipynb)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/DahnJ/H3-Pandas/HEAD?filepath=%2Fnotebook%2Fexample.ipynb)
[![image](https://img.shields.io/pypi/v/h3pandas.svg)](https://pypi.python.org/pypi/h3pandas)
[![image](https://pepy.tech/badge/h3pandas)](https://pepy.tech/project/h3pandas)
[![Anaconda-Server Badge](https://anaconda.org/dahn/h3pandas/badges/downloads.svg)](https://anaconda.org/dahn/h3pandas)
[![image](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

&nbsp;


---

<h3 align="center">
  ⬢ <a href="https://mybinder.org/v2/gh/DahnJ/H3-Pandas/HEAD?filepath=%2Fnotebook%2Fexample.ipynb">Try it out</a> ⬢
</h3>

---
<p align="center">
    <a href=""><img src="https://i.imgur.com/FLeAqjL.gif" alt="example usage" width="450"></a>
</p>


## Installation
### pip
```bash
pip install h3pandas
```

### conda
```bash
conda config --add channels conda-forge  # Most dependencies are on conda-forge
conda install -c dahn h3pandas
```

## Usage examples

```python
# Prepare data
>>> import pandas as pd
>>> import h3pandas
>>> df = pd.DataFrame({'lat': [50, 51], 'lng': [14, 15]})
```
### H3 api
`h3pandas` automatically applies H3 functions to both Pandas Dataframes and GeoPandas Geodataframes



```python
>>> resolution = 10
>>> df = df.h3.geo_to_h3(resolution)
>>> df

| h3_10           |   lat |   lng |
|:----------------|------:|------:|
| 8a1e30973807fff |    50 |    14 |
| 8a1e2659c2c7fff |    51 |    15 |

>>> df = df.h3.h3_to_geo_boundary()
>>> df

| h3_10           |   lat |   lng | geometry        |
|:----------------|------:|------:|:----------------|
| 8a1e30973807fff |    50 |    14 | POLYGON ((...)) |
| 8a1e2659c2c7fff |    51 |    15 | POLYGON ((...)) |
```

### Aggregate functions
`h3pandas` also provides common aggregations in a simple API.

```python
# Set up data
>>> import numpy as np
>>> import pandas as pd
>>> np.random.seed(1729)
>>> df = pd.DataFrame({
>>>   'lat': np.random.uniform(50, 51, 100),
>>>   'lng': np.random.uniform(14, 15, 100),
>>>   'value': np.random.poisson(100, 100)})
>>> })
```

```python
# Aggregate values by their location and sum
>>> df = df.h3.geo_to_h3_aggregate(3)
>>> df

| h3_03           |   value |
|:----------------|--------:|
| 831e30fffffffff |     102 |
| 831e34fffffffff |     189 |
| 831e35fffffffff |    8744 |
| 831f1bfffffffff |    1040 |

# Aggregate to a lower H3 resolution
>>> df.h3.h3_to_parent_aggregate(2)

| h3_02           |   value |
|:----------------|--------:|
| 821e37fffffffff |    9035 |
| 821f1ffffffffff |    1040 |
```

## API
For a full API documentation and more usage examples, see the [documentation](https://h3-pandas.readthedocs.io/en/latest/).

## Development
This package is under active development, **suggestions and contributions are very welcome**!

In particular, the next steps are:
- [ ] Improve documentation, examples
- [ ] Greater coverage of the H3 API

Additional possible directions
- [ ] Allow for alternate h3-py APIs such as [memview_int](https://github.com/uber/h3-py#h3apimemview_int)
- [ ] Performance improvements through [Cythonized h3-py](https://github.com/uber/h3-py/pull/147)
- [ ] [Dask](https://github.com/dask/dask) integration trough [dask-geopandas](https://github.com/geopandas/dask-geopandas) (experimental as of now)
