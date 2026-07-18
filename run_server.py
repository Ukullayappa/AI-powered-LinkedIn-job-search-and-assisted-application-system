import asyncio
import sys

import uvicorn


if __name__ == "__main__":
    # Playwright starts a browser subprocess.
    # Windows requires ProactorEventLoop for subprocess support.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsProactorEventLoopPolicy()
        )

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        loop="asyncio",
    )