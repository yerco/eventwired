from demo_app.controllers.cors_test_controller import cors_test_controller
from demo_app.controllers.hello_controller import hello_controller
from demo_app.controllers.page_controller import page_detail_controller
from demo_app.controllers.home_controller import home_controller
from demo_app.controllers.login_controller import login_controller
from demo_app.controllers.register_controller import register_controller
from demo_app.controllers.logout_controller import logout_controller
from demo_app.controllers.welcome_controller import welcome_controller
from demo_app.controllers.render_chat_room_controller import render_chat_room_controller
from demo_app.controllers.chat_room_controller import chat_room_controller
# from demo_app.controllers.queries_books_controller import queries_books_controller
# from demo_app.controllers.commands_books_controller import commands_books_controller
#from demo_app.controllers.api_controllers import api_create_user_controller, api_login_controller, api_protected_controller


async def register_routes(routing_service):
    routing_service.add_route('/', 'GET', welcome_controller)
    routing_service.add_route('/favicon.ico', 'GET', welcome_controller)
    routing_service.add_route('/hello', 'GET', hello_controller, requires_auth=True)
    routing_service.add_route('/home', 'GET', home_controller)
    routing_service.add_route('/page/<int:id>', 'GET', page_detail_controller)
    routing_service.add_route('/login', ['GET', 'POST'], login_controller)
    routing_service.add_route('/register', ['GET', 'POST'], register_controller)
    routing_service.add_route('/logout', 'GET', logout_controller)
    routing_service.add_route('/chat_room', 'GET', render_chat_room_controller)
    routing_service.add_route('/myws', 'WEBSOCKET', chat_room_controller)
    routing_service.add_route('/cors', ['GET', 'POST', 'OPTIONS'], cors_test_controller)
    # # Command
    # routing_service.add_route('/books/action/add', ['POST'], commands_books_controller)
    # routing_service.add_route('/books/<str:title>/edit', ['POST'], commands_books_controller)
    # routing_service.add_route('/books/<str:title>/delete', ['POST'], commands_books_controller)
    # # Query
    # routing_service.add_route('/books', ['GET'], queries_books_controller)
    # routing_service.add_route('/books/action/add', ['GET'], queries_books_controller)
    # routing_service.add_route('/books/<str:title>', ['GET'], queries_books_controller)
    # routing_service.add_route('/books/<str:title>/edit', ['GET'], queries_books_controller)  # just to show the form
    # # Example API JWT
    #routing_service.add_route('/api/create', ['POST'], api_create_user_controller)
    #routing_service.add_route('/api/login', ['POST'], api_login_controller)
    #routing_service.add_route('/api/protected', ['GET'], api_protected_controller, requires_jwt_auth=True)

