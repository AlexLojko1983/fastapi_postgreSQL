from typing import Union
from pydantic import BaseModel
import contextlib
from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from bson import ObjectId
from fastapi.encoders import jsonable_encoder

app = FastAPI()
client = MongoClient('mongodb://localhost:27017/')
db = client['courses']

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None



@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}

@app.get('/courses')
async def get_courses(sort_by: str = 'date', domain=None):
    for course in db.courses.find():
        total = 0
        count = 0
        for chapter in course['chapters']:
            with contextlib.suppress(KeyError):
                total += chapter['rating']['total']
                count += chapter['rating']['count']
        db.courses.update_one({"id": course['id']}, {'$set':{"rating": {'total': total, 'count': count}}})

    #Sort by
    if sort_by == 'date':
        sort_field = 'date'
        sort_order = -1
    elif sort_by == 'rating':
        sort_field = 'rating.total'
        sort_order = -1
    else:
        sort_field = 'name'
        sort_order = 1

    query = {}
    if domain:
        query['domain'] = domain

    courses = db.courses.find(query, {'name': 1, 'date': 1, 'description': 1, 'rating': 1, 'id': 0}).sort(sort_field, sort_order)
    return list(courses)





