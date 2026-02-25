# Makefile

# Specify the Python version
PYTHON_VERSION := python3.11
LAMBDA_VENV := .lambda_venv
PACKAGE_NAME := lambda_function.zip
# Add other files separated by spaces if necessary
LAMBDA_FUNCTION := lambda_download_csv.py

# Default target executed when no arguments are given to make.
default: clean package

# Setup a virtual environment
venv:
	$(PYTHON_VERSION) -m venv $(LAMBDA_VENV) --without-pip
	curl -sS https://bootstrap.pypa.io/get-pip.py | $(LAMBDA_VENV)/bin/python3
	$(LAMBDA_VENV)/bin/pip install -U pip

# Install dependencies into the virtual environment
dependencies: venv
	$(LAMBDA_VENV)/bin/pip install -r requirements-lambda.txt

# Package the virtual environment libraries and your lambda function into a zip
package: dependencies
	# Adding python packages (find the actual python version in venv)
	@PYTHON_DIR=$$(ls $(LAMBDA_VENV)/lib/ | head -n 1); \
	cd $(LAMBDA_VENV)/lib/$$PYTHON_DIR/site-packages; zip -r9 $(CURDIR)/$(PACKAGE_NAME) .
	# Adding your lambda function and any additional files
	zip -gj $(PACKAGE_NAME) ./app/src/lambda/$(LAMBDA_FUNCTION)

# Clean up the environment
clean:
	rm -rf $(LAMBDA_VENV)
	rm -f $(PACKAGE_NAME)

.PHONY: default venv dependencies package