<img align="left" src="https://i.imgur.com/OH8DoTA.png" alt="H3 Logo" width="500">


&nbsp;

# H3-Pandas ⬢ 🐼
Integrates [H3](https://github.com/uber/h3-py) with  [GeoPandas](https://github.com/geopandas/geopandas)
and [Pandas](https://github.com/pandas-dev/pandas).
[![image](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DahnJ/H3-Pandas/blob/master/notebook/00-intro.ipynb)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/DahnJ/H3-Pandas/HEAD?filepath=%2Fnotebook%2F00-intro.ipynb)
[![image](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/pip/badge/?version=stable)](https://pip.pypa.io/en/stable/?badge=stable)

&nbsp;


---

<h3 align="center">
  ⬢ <a href="https://mybinder.org/v2/gh/DahnJ/H3-Pandas/HEAD?filepath=%2Fnotebook%2F00-intro.ipynb">Try it out</a> ⬢
</h3>

---
<p align="center">
    <a href="https://github.com/DahnJ/H3-Pandas"><img src="https://i.imgur.com/GZWsC8G.gif" alt="example usage" width="450"></a>
</p>


## Installation
### pip
[![image](https://img.shields.io/pypi/v/h3pandas.svg)](https://pypi.python.org/pypi/h3pandas)
```bash
pip install h3pandas
```

### conda
[![conda-version](https://anaconda.org/conda-forge/h3pandas/badges/version.svg)]()
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/h3pandas/badges/downloads.svg)](https://anaconda.org/conda-forge/h3pandas)
```bash
conda install -c conda-forge h3pandas
```

## Usage examples

### H3 API
`h3pandas` automatically applies H3 functions to both Pandas Dataframes and GeoPandas Geodataframes

```python
# Prepare data
>>> import pandas as pd
>>> import h3pandas
>>> df = pd.DataFrame({'lat': [50, 51], 'lng': [14, 15]})
```

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

### H3-Pandas Extended API
`h3pandas` also provides some extended functionality out-of-the-box, 
often simplifying common workflows into a single command.

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

| h3_03           |   value | geometry        |
|:----------------|--------:|:----------------|
| 831e30fffffffff |     102 | POLYGON ((...)) |
| 831e34fffffffff |     189 | POLYGON ((...)) |
| 831e35fffffffff |    8744 | POLYGON ((...)) |
| 831f1bfffffffff |    1040 | POLYGON ((...)) |

# Aggregate to a lower H3 resolution
>>> df.h3.h3_to_parent_aggregate(2)

| h3_02           |   value | geometry        |
|:----------------|--------:|:----------------|
| 821e37fffffffff |    9035 | POLYGON ((...)) |
| 821f1ffffffffff |    1040 | POLYGON ((...)) |
```


### Further examples
For more examples, see the 
[example notebooks](https://nbviewer.jupyter.org/github/DahnJ/H3-Pandas/tree/master/notebook/).

## API
For a full API documentation and more usage examples, see the 
[documentation](https://h3-pandas.readthedocs.io/en/latest/).

## Development
H3-Pandas cover the basics of the H3 API, but there are still many possible improvements.

**Any suggestions and contributions are very welcome**!

In particular, the next steps are:
- [ ] Improvements & stability of the "Extended API", e.g. `k_ring_smoothing`. 

Additional possible directions
- [ ] Allow for alternate h3-py APIs such as [memview_int](https://github.com/uber/h3-py#h3apimemview_int)
- [ ] Performance improvements through [Cythonized h3-py](https://github.com/uber/h3-py/pull/147)
- [ ] [Dask](https://github.com/dask/dask) integration through [dask-geopandas](https://github.com/geopandas/dask-geopandas) (experimental as of now)

See [issues](https://github.com/DahnJ/H3-Pandas/issues) for more.
