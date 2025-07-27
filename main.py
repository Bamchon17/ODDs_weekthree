from fastapi import FastAPI, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi import status
from fastapi.templating import Jinja2Templates
from fastapi import Request
from typing import List
from pydantic import BaseModel
from datetime import datetime
import json
from pathlib import Path
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class Todo(BaseModel):
    id: int
    task: str
    done: bool = False
    category: str = "General"
    due_date: str = None  # Store as string for JSON compatibility
    priority: str = "Medium"

todos: List[Todo] = []
next_id = 1

def load_todos():
    global todos, next_id
    if Path("todos.json").exists():
        with open("todos.json", "r") as f:
            todos_data = json.load(f)
            todos = [Todo(**data) for data in todos_data]
            next_id = max([todo.id for todo in todos] or [0]) + 1

def save_todos():
    with open("todos.json", "w") as f:
        json.dump([todo.dict() for todo in todos], f)
        
class TodoService:
    def create_todo(self, task: str, category: str, due_date: str, priority: str):
        global todos, next_id
        todo = Todo(id=next_id, task=task, category=category, due_date=due_date, priority=priority)
        todos.append(todo)
        next_id += 1
        save_todos()
        return todo

    def mark_done(self, todo_id: int):
        global todos
        for todo in todos:
            if todo.id == todo_id:
                todo.done = True
                save_todos()
                return True
        return False

    def delete_todo(self, todo_id: int):
        global todos
        for i, todo in enumerate(todos):
            if todo.id == todo_id:
                todos.pop(i)
                save_todos()
                return True
        return False


todo_service = TodoService()

@app.on_event("startup")
async def startup_event():
    load_todos()

@app.get("/", response_class=templates.TemplateResponse)
async def read_root(request: Request, show_all: bool = True, search_query: str = None):
    if search_query:
        display_todos = [todo for todo in todos if search_query.lower() in todo.task.lower()]
    else:
        display_todos = todos if show_all else [todo for todo in todos if not todo.done]
    return templates.TemplateResponse("index.html",
            {"request": request, 
             "todos": display_todos, 
             "show_all": show_all,
             "now": datetime.now(),
             "search_query": search_query})

@app.post("/create-todo", response_class=RedirectResponse)
async def create_todo(task: str = Form(...), category: str = Form("General"), due_date: str = Form(None), priority: str = Form("Medium"), service: TodoService = Depends(lambda: todo_service)):
    service.create_todo(task, category, due_date, priority)
    return RedirectResponse("/?show_all=true", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/mark-done/{todo_id}", response_class=RedirectResponse)
async def mark_done(todo_id: int, service: TodoService = Depends(lambda: todo_service)):
    if not service.mark_done(todo_id):
        return RedirectResponse("/?show_all=false", status_code=status.HTTP_303_SEE_OTHER, headers={"error": "Todo not found"})
    return RedirectResponse("/?show_all=false", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/delete-todo/{todo_id}", response_class=RedirectResponse)
async def delete_todo(todo_id: int, service: TodoService = Depends(lambda: todo_service)):
    if not service.delete_todo(todo_id):
        return RedirectResponse("/?show_all=true", status_code=status.HTTP_303_SEE_OTHER, headers={"error": "Todo not found"})
    return RedirectResponse("/?show_all=true", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/search", response_class=templates.TemplateResponse)
async def search_todos(request: Request, query: str = Form(...)):
    return await read_root(request, show_all=True, search_query=query)