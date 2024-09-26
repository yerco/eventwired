async def startup(di_container, user_startup_callback=None):
    try:
        orm_service = await di_container.get('ORMService')
        await orm_service.init()
        await orm_service.create_tables()

        routing_service = await di_container.get('RoutingService')

        if routing_service is None:
            raise ValueError("RoutingService is not configured properly")

        await routing_service.start_routing()

        # Log and call the user-defined startup callback, if provided
        if user_startup_callback:
            await user_startup_callback(di_container)

    except Exception as e:
        # Print the exception and re-raise it with more context
        print(f"Error during startup initialization: {e}")
        raise


async def shutdown(di_container):
    try:
        orm_service = await di_container.get('ORMService')
        await orm_service.cleanup()

        websocket_service = await di_container.get('WebSocketService')
        await websocket_service.broadcast_shutdown()
    except Exception as e:
        print(f"Error during ORM/WebSocket cleanup: {e}")


async def handle_lifespan_events(scope, receive, send, request, di_container, user_startup_callback=None):
    try:
        while True:
            message = await receive()
            if message['type'] == 'lifespan.startup':
                await startup(di_container, user_startup_callback)  # Pass user callback here
                await send({'type': 'lifespan.startup.complete'})
            elif message['type'] == 'lifespan.shutdown':
                await shutdown(di_container)
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
