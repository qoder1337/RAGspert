from fastapi.templating import Jinja2Templates
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
