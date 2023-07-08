from fastapi import FastAPI, Query, Path, HTTPException, status, Body, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

from starlette.responses import HTMLResponse

from database import cars

templates = Jinja2Templates(directory='templates')


class Car(BaseModel):
    make: Optional[str]
    model: Optional[str]
    year: Optional[int] = Field(...,ge=1970,lt=2022)
    price: Optional[float]
    engine: Optional[str] = "V4"
    autonomous: Optional[bool]
    sold: Optional[List[str]]


app = FastAPI()

app.mount('/static', StaticFiles(directory="static"), name='static')

@app.get("/", response_class=RedirectResponse)
async def root(request: Request):
    return RedirectResponse(url="/cars")


@app.get('/cars', response_class=HTMLResponse) # тут указываем какой будет переменная response
async def get_cars(request: Request, number: Optional[str] = Query("10",max_length=3)):
    response = []
    for id, car in list(cars.items())[:int(number)]: # делает срез ДО query параметра
        response.append((id, car))
    return templates.TemplateResponse('index.html', {"request": request, "cars": response})


@app.post('/search', response_class=RedirectResponse)
async def search_cars(id: str = Form(...)):
    return RedirectResponse("/cars/" + id, status_code=302)


@app.get("/cars/{id}", response_class=HTMLResponse)
def get_car_by_id(request: Request, id: int = Path(...,ge=0,lt=1000)):
    car = cars.get(id)
    response = templates.TemplateResponse("search.html", {"request": request, "car": car, "id": id, "title": "Search Car"})
    if not car:
        response.status_code = status.HTTP_404_NOT_FOUND
    return response




@app.post('/cars', status_code=status.HTTP_201_CREATED)
async def add_cars(body_cars: List[Car], min_id: Optional[int] = Body(0)):
    if len(body_cars) < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No card to add")
    min_id = len(cars.values()) + min_id # условно 5 + 0
    for car in body_cars:
        while cars.get(min_id): #пока может достать такой ключ(5) достань
            min_id += 1 # прибавь + 1 (6)
        cars[min_id] = car
        min_id += 1


@app.put("/cars/{id}", response_model=Dict[str, Car])
async def update_car(id: int, car: Car = Body(...)):
    stored = cars.get(id) # достаем машину по id
    if not stored:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not find car with given ID")
    stored = Car(**stored) # создаем новый экземпляр и распаковываем в него старый
    new = car.dict(exclude_unset=True) # создаст словарь без значений по умолчанию или пусты
    new = stored.copy(update=new) # копирует stored при этом заменяя значения
    cars[id] = jsonable_encoder(new) # Преобразуйте скопированную модель во что-то, что можно сохранить в вашей БД
    response = {}
    response[id] = cars[id] # сохраняем результат для вывода
    return response


@app.delete('/cars/{id}')
async def delete_car(id: int):
    if not cars.get(id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not find car by ID.")
    del cars[id]

