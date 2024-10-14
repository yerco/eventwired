class ErrorHandlerService:
    def __init__(self, template_service=None):
        self.template_service = template_service

    async def render_error(self, event, status_code, default_message):
        send = event.data.get('send')

        if self.template_service:
            try:
                # Attempt to render a custom template for the error code (e.g., 404.html, 405.html)
                template_name = f"errors/{status_code}.html"
                content = self.template_service.render_template(template_name, {"status_code": status_code})
            except FileNotFoundError:
                # If the template does not exist, use the default message
                content = default_message
        else:
            # If no template service, fallback to the default message
            content = default_message

        # Send the error response
        await send({
            'type': 'http.response.start',
            'status': status_code,
            'headers': [
                [b'content-type', b'text/html'],
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': content.encode(),
        })

        event.data['response_already_sent'] = True
