import aiohttp
import logging

logger = logging.getLogger('uvicorn')


async def get_ngrok_http_tunnel() -> str:
    """Helper function to retrieve http tunnel from local ngrok instance

    Returns:
        str: http host address without `http://` part
    """
    host = None
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get('http://127.0.0.1:4040/api/tunnels')
            data = await response.json()
            hosts = [x.get('public_url') for x in data['tunnels']
                     if not 'https' in x.get('public_url')]
            if hosts:
                host = hosts[0].replace('http://', '')
    except Exception as exc:
        logger.warn(f'Error during Ngrok tunnel retrieval: {exc}')
    return host
