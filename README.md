# YASGI

A lightweight, async-first web framework built with modern web development in mind.

## Tools of the trade
- Python 3.11.8

## How to run

1. Clone this repository
    ```bash
    $ git clone https://github.com/yerco/yasgi.git
    ```

2. Create a virtualenv and activate it (optional)
   ```bash
   $ python -m venv venv
   
    $ source venv/bin/activate
   ```
   Preferably do `$ source /full/path/to/venv/bin/activate)` I saw problems with uvicorn and pyenv

3. Install the required packages
   ```bash
   $ pip install -r requirements.txt
   ```

4. Run the server
   2.1 Using uvicorn
   ```bash
   $ uvicorn demo_app.app:app [--reload]
   ```
And go to http://127.0.0.1:8000

## Testing
   ```bash
   $ pytest
   
   $ pytest --cov=src tests/
   
   $ pytest --cov=src --cov-report=html
   ```

## User-Centric Framework Design
YASGI is designed to give you full control over your application, making it easy to use the tools provided by the
framework without enforcing a rigid structure. This user-centric approach allows you to integrate features like
routing, event handling, and services in a way that best suits your application.

I encourage you to explore the demo_app provided with the framework. The `demo_app` serves as an example of
how to structure your project using the framework’s components, including dependency injection, routing,
templating, and more. By examining and running the `demo_app`, you’ll get a clear understanding of how to
leverage the framework’s capabilities to build your own ASGI applications.

## Important Note
For most developers, everything needed to build your project is found within the `demo_app` folder.
It serves as the go-to example for project structure and implementation. The `src` folder, on the other hand,
contains the internal framework workings and is generally not necessary to modify when building your application.
