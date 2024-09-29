# YASGI

A lightweight, async-first web framework built with modern web development in mind. **This is work in progress** focused first on educational purposes.

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

   Currently, the server only supports **Uvicorn**.

   **Using Uvicorn:**
   ```bash
   $ python run_server.py [--reload] [--host 127.0.0.1] [--port 8000]
   ```
   
   Visit the server at http://127.0.0.1:8000

   Note: Daphne support is not yet implemented.

## Testing
   ```bash
   $ pytest
   
   $ pytest --cov=src tests/
   
   $ pytest --cov=demo_app --cov-report=html
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

## Example Routes
Define routes easily with Python:
   ```python
   from demo_app.controllers.welcome_controller import welcome_controller
   
   def register_routes(routing_service):
       routing_service.add_route('/', 'GET', welcome_controller)
   ```
   
## Example Controllers
Controllers are simple Python functions that handle requests and return responses. They can be as simple or complex
as needed.
   ```python
   from src.controllers.base_controller import BaseController
   from src.event_bus import Event
   from demo_app.di_setup import di_container
   
   async def welcome_controller(event: Event):
      controller = BaseController(event)
      template_service = await di_container.get('TemplateService')
      rendered_content = template_service.render_template('welcome.html', {})
      await controller.send_html(rendered_content)
   ```
   
## Real-Time Chat Room Example
With YASGI, you can create a real-time chat room with just a few lines of code. The demo_app includes a chat room
available at `/chat_room`. Below is all you need to write to set up a chat room using WebSockets:

   ```python
   from src.controllers.base_controller import BaseController
   from src.event_bus import Event
   from demo_app.di_setup import di_container

   async def chat_room_controller(event: Event):
      websocket_service = await di_container.get('WebSocketService')
      controller = WebSocketController(event)
      websocket_service.register_client(controller)
   
      async def on_message(message):
         if message not in {"websocket.connect", "websocket.disconnect"}:
            broadcast_message = f"User: {message}"
            await websocket_service.broadcast_message(broadcast_message)
      
      await websocket_service.accept_client_connection(controller)
      await websocket_service.listen(controller, on_message)
   ```

This, along with a simple HTML template and route setup, is enough to get your chat room running.

### Contribute

Feedback is warmly welcomed, contributions, or suggestions to improve YASGI. Whether it's reporting a bug, suggesting a feature, or sharing your thoughts, your input is invaluable to me.

If you'd like to contribute:
- Fork the repository.
- Create a new branch for your feature or bug fix.
- Submit a pull request with a description of your changes.

Please feel free to open an issue if you have questions or ideas. Every piece of feedback helps us make YASGI better!
