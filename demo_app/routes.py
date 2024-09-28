from demo_app.controllers.hello_controller import hello_controller
from demo_app.controllers.page_controller import page_detail_controller
from demo_app.controllers.home_controller import home_controller
from demo_app.controllers.login_controller import login_controller
from demo_app.controllers.register_controller import register_controller
from demo_app.controllers.logout_controller import logout_controller
from demo_app.controllers.welcome_controller import welcome_controller
from demo_app.controllers.render_chat_room_controller import render_chat_room_controller
from demo_app.controllers.chat_room_controller import chat_room_controller

def register_routes(routing_service):
    routing_service.add_route('/', 'GET', welcome_controller)
    routing_service.add_route('/hello', 'GET', hello_controller, requires_auth=True)
    routing_service.add_route('/home', 'GET', home_controller)
    routing_service.add_route('/page/<int:id>', 'GET', page_detail_controller)
    routing_service.add_route('/login', ['GET', 'POST'], login_controller)
    routing_service.add_route('/register', ['GET', 'POST'], register_controller)
    routing_service.add_route('/logout', 'GET', logout_controller)
    routing_service.add_route('/websocket_test', 'GET', render_chat_room_controller)
    routing_service.add_route('/myws', 'WEBSOCKET', chat_room_controller)
