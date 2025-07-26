from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import status
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class Todo(BaseModel):
    id: int
    task: str
    done: bool = False

todos: List[Todo] = []
next_id = 1

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, show_all: bool = True):
    display_todos = todos if show_all else [todo for todo in todos if not todo.done]
    return templates.TemplateResponse("index.html", {"request": request, "todos": display_todos, "show_all": show_all})

@app.post("/create-todo", response_class=RedirectResponse)
async def create_todo(task: str = Form(...)):
    global next_id
    todo = Todo(id=next_id, task=task)
    todos.append(todo)
    next_id += 1
    return RedirectResponse("/?show_all=true", status_code=status.HTTP_303_SEE_OTHER)

@app.put("/mark-done/{todo_id}", response_class=RedirectResponse)
async def mark_done(todo_id: int):
    for todo in todos:
        if todo.id == todo_id:
            todo.done = True
            return RedirectResponse("/?show_all=false", status_code=status.HTTP_303_SEE_OTHER)
    raise HTTPException(status_code=404, detail="Todo not found")

@app.delete("/delete-todo/{todo_id}", response_class=RedirectResponse)
async def delete_todo(todo_id: int):
    for i, todo in enumerate(todos):
        if todo.id == todo_id:
            todos.pop(i)
            return RedirectResponse("/?show_all=true", status_code=status.HTTP_303_SEE_OTHER)
    raise HTTPException(status_code=404, detail="Todo not found")

@app.get("/unfinished", response_class=HTMLResponse)
async def show_unfinished(request: Request):
    return await read_root(request, show_all=False)