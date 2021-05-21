#/bin/bash
pytest --cov-report html --cov h3pandas
flake8 . 
# xdg-open htmlcov/h3pandas_h3pandas_py.html
