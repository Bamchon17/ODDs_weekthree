from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import status
from pydantic import BaseModel
from typing import List

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# create a Class to store items
class Todo(BaseModel):
    id: int
    task: str
    done: bool = False

# Temporary storage for todos (in-memory)
todos: List[str] = []
next_id = 1

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, show_all: Optional[bool] = True):
    if show_all:
        display_todos = todos
    return templates.TemplateResponse("index.html", {"request": request, "todos": todos})

@app.post("/create-todo")
def create_todo(item: str = Form(...)):
    todos.append(item)
    return RedirectResponse("/", status_code=303)

