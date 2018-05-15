# Tests for scrapyrt-aftership

All tests for aftership-courier-api are in folder tests-aftership

There are 3 different test files: test\_aftership\_resource.py, test\_AfterShipErrorPage.py, test\_HTTP\_status\_code\_and\_meta\_code.py, each of it tests different part of scrapyrt for AfterShip.

## Install the dependency

First you may need to install the py.test module, it will make the result more beautiful and readable.

```
pip install pytest
```

Also, you need to install pytest-cov if you want to see the test coverage reports.

```
pip install pytest-cov
```

## Run the tests

After the install of the dependency, you can simply run all the test at root directory by:

```
python -m py.test -v tests-aftership/
```

you can also run single test by add single file name, 

e.g.:

```
python -m py.test -v tests-aftership/test_aftership_resource.py
```

### Coverage Report

If you want to see the coverage report of your code:

```
python -m py.test --cov-report html --cov=..scrapyrt/ tests-aftership/
```

The report folder 'htmlcov' will automatically created under you root directory.