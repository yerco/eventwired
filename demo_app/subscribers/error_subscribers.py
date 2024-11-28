from src.core.request import Request
from src.core.event_bus import Event

from demo_app.di_setup import di_container


async def handle_403_event(event: Event):
    request = event.data['request']
    send = event.data['send']
    error_page = f"<html><body><h1>USER SIDE YASGI 403 Forbidden: {request.path}</h1></body></html>"
    await send({
        'type': 'http.response.start',
        'status': 403,
        'headers': [[b'content-type', b'text/html']],
    })
    await send({
        'type': 'http.response.body',
        'body': error_page.encode(),
    })

    event.data['response_already_sent'] = True


async def handle_404_event(event: Event):
    template_service = await di_container.get('TemplateService')
    request: Request = event.data['request']
    context = {}
    rendered_content = template_service.render_template('404.html', context)
    send = event.data['send']
    await send({
        'type': 'http.response.start',
        'status': 404,
        'headers': [[b'content-type', b'text/html']],
    })
    await send({
        'type': 'http.response.body',
        'body': rendered_content.encode(),
    })
    event.data['response_already_sent'] = True


async def handle_405_event(event: Event):
    request = event.data['request']
    send = event.data['send']
    error_page = f"<html><body><h1>USER SIDE YASGI 405 Method Not Allowed: {request.path}</h1></body></html>"
    await send({
        'type': 'http.response.start',
        'status': 405,
        'headers': [[b'content-type', b'text/html']],
    })
    await send({
        'type': 'http.response.body',
        'body': error_page.encode(),
    })
    event.data['response_already_sent'] = True


async def handle_500_event(event: Event):
    request = event.data['request']
    send = event.data['send']
    error_page = f"<html><body><h1>USER SIDE YASGI 500 error: {request.path}</h1></body></html>"
    await send({
        'type': 'http.response.start',
        'status': 405,
        'headers': [[b'content-type', b'text/html']],
    })
    await send({
        'type': 'http.response.body',
        'body': error_page.encode(),
    })
    event.data['response_already_sent'] = True


async def handle_no_csrf_event(event: Event):
    request = event.data['request']
    send = event.data['send']
    response_body = f"""
    <html>
        <body>
            <h1>403 Forbidden: CSRF token missing</h1>
            <p>The request to {request.path} was rejected due to a missing CSRF token.</p>
            <p>
                <a href="{request.path}" >Reload the page</a>
            </p>
        </body>
    </html>
    """
    await send({
        'type': 'http.response.start',
        'status': 403,
        'headers': [[b'content-type', b'text/html']],
    })
    await send({
        'type': 'http.response.body',
        'body': response_body.encode(),
    })
    event.data['response_already_sent'] = True


async def websocket_connection_close(event: Event):
    pass
