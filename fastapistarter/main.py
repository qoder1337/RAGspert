import uvicorn
from src.config import SET_CONF


if __name__ == "__main__":
    app_greeting = f"{SET_CONF.APP_NAME}"
    show_environment = f"ENVIRONMENT: {SET_CONF.APP_ENV}"
    print(f"|| {app_greeting} ||")
    print(f"|| {show_environment} ||")
    uvicorn.run("src.load_app:app", host="localhost", port=1337, reload=SET_CONF.RELOAD)
