async def handle_lifespan_events(scope, receive, send):
    try:
        while True:
            message = await receive()
            if message['type'] == 'lifespan.startup':
                await send({'type': 'lifespan.startup.complete'})
            elif message['type'] == 'lifespan.shutdown':
                await send({'type': 'lifespan.shutdown.complete'})
                return
            else:
                # Lifespan protocol unsupported or unrecognized message
                print(f"Unsupported lifespan message: {message}")
                await send({'type': 'lifespan.shutdown.complete'})
    except Exception as e:
        print(f"Error during lifespan handling: {e}")
        await send({
            'type': 'lifespan.shutdown.complete',
        })
