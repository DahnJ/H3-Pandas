ENV_NAME := h3-pandas
ENVIRONMENT := environment.yml
ENVIRONMENT_DEV := environment-dev.yml

install: _install _update_dev _install_package_editable

_install:
	mamba env create -n $(ENV_NAME) -f $(ENVIRONMENT)

_update_dev: 
	mamba env update -n $(ENV_NAME) -f $(ENVIRONMENT_DEV)

_install_package_editable: 
	mamba run -n $(ENV_NAME) python -m pip install -e .
