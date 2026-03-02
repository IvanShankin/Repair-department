import asyncio
import threading

def start_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def init_new_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()

    threading.Thread(
        target=start_loop,
        args=(loop,),
        daemon=True
    ).start()

    return loop