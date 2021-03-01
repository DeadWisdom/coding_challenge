# Coding Challenge App

This is my submission for the coding challenge.

I deviated from Flask because I decided to run the tasks as simple GET requests
rather than a more complicated job system. This meant I needed to send out
requests to the API sites efficiently and chose to do this with async requests
via the httpx library. Using asyncio with Flask is not recommended, so I used
the closest framework that also supported python 3.6: sanic

## Github Throttling

If you're doing this test a bunch, github throttles you pretty quick. In the
`app/github.py` there's a `HTTPX_AUTH` constant, you can set your username
and a personal access token: https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token

If I had more time, I'd make that a setting, sorry.

## Install:

Create a virtual environment, if you want.

```
python -m venv env
source env/bin/activate
```

Pip install from the requirements file.

```
pip install -r requirements.txt
```

Sanic takes a while, thanks to uvloop, and might fail; see here:
https://sanic.readthedocs.io/en/stable/sanic/getting_started.html

### Running the tests

```
pytest
```

## Running the code

### Spin up the service

```
# start up local server
python -m run
```

### Making Requests

```
curl -i "http://127.0.0.1:8000/health-check"
```

```
curl -i "http://127.0.0.1:8000/github/mailchimp"
```

```
curl -i "http://127.0.0.1:8000/bitbucket/mailchimp"
```

```
curl -i "http://127.0.0.1:8000/merged-profiles?github=mailchimp&bitbucket=mailchimp"
```

## What'd I'd like to improve on...

- Add an open-api spec with well defined models
- Add more data validation
- Add authentication handling
- Add type hints
- Patch httpx requests to return mocked out data for tests so we can test
  more precisely
