from starlette.endpoints import HTTPEndpoint

from star import settings


class Homepage(HTTPEndpoint):
    async def get(self, request):
        response = settings.templates.TemplateResponse(
            'index.html', {'request': request, 'host': settings.ADDRESS}
        )
        return response
