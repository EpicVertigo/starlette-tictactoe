import uvicorn

from star import create_app, settings

app = create_app()

if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=settings.PORT)
