# Tests for scrapyrt-aftership

All tests for aftership-courier-api are in folder tests-aftership

There are 3 different test files: test\_aftership\_resource.py, test\_AfterShipErrorPage.py, test\_HTTP\_status\_code\_and\_meta\_code.py, each of it tests different part of scrapyrt for AfterShip.

## Install the dependency

First, please install denpendencies by pipenv:

```
pipenv install -d
```

## Run the tests

After the install of the dependency, you can simply run all the test at root directory by:

```
pipenv run python -m pytest -v tests-aftership/
```

you can also run single test by add single file name, 

e.g.:

```
pipenv run python -m pytest -v tests-aftership/test_aftership_resource.py
```

### Coverage Report

If you want to see the coverage report of your code:

```
pipenv run python -m pytest --cov-report html --cov=..scrapyrt/ tests-aftership/
```

The report folder 'htmlcov' will automatically created under you root directory.