from src.core.event_bus import Event


async def handle_404_event(event: Event):
    request = event.data['request']
    send = event.data['send']
    error_page = f"<html><body><h1>YASGI 404 Not Found: {request.path}</h1></body></html>"
    await send({
        'type': 'http.response.start',
        'status': 404,
        'headers': [[b'content-type', b'text/html']],
    })
    await send({
        'type': 'http.response.body',
        'body': error_page.encode(),
    })


async def handle_405_event(event: Event):
    request = event.data['request']
    send = event.data['send']
    error_page = f"<html><body><h1>YASGI 405 Method Not Allowed: {request.path}</h1></body></html>"
    await send({
        'type': 'http.response.start',
        'status': 405,
        'headers': [[b'content-type', b'text/html']],
    })
    await send({
        'type': 'http.response.body',
        'body': error_page.encode(),
    })


async def handle_500_event(event: Event):
    request = event.data['request']
    send = event.data['send']
    error_page = f"<html><body><h1>YASGI 500 error: {request.path}</h1></body></html>"
    await send({
        'type': 'http.response.start',
        'status': 405,
        'headers': [[b'content-type', b'text/html']],
    })
    await send({
        'type': 'http.response.body',
        'body': error_page.encode(),
    })
