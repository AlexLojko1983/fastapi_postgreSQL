from typing import Union

from bson.errors import InvalidId
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
async def get_courses(sort_by: str = 'date', domain: str=None):
    for course in db.courses.find():
        total = 0
        count = 0
        for chapter in course['chapters']:
            with contextlib.suppress(KeyError):
                total += chapter['rating']['total']
                count += chapter['rating']['count']
        db.courses.update_one({"id": course['_id']}, {'$set':{"rating": {'total': total, 'count': count}}})

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

    courses = db.courses.find(query, {'name': 1, 'date': 1, 'description': 1, 'rating': 1, '_id': 0}).sort(sort_field, sort_order)
    return list(courses)

@app.get('/courses/{course_id}')
async def get_course(course_id: str):
    try:
        course_id = ObjectId(course_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail='Invalid course ID format')

    course = db.courses.find_one({'_id':ObjectId(course_id)},{'_id': 0, 'chapters': 0})
    if not course:
        raise HTTPException(status_code=404, detail='Course not found')

    try:
        course['rating']=course['rating']['total']
    except KeyError:
        course['rating'] = 'Not rated yet'

    return course


@app.get('/courses/{course_id}/{chapter_id}')
async def get_chapter(course_id: str, chapter_id: str):
    try:
        course_id = ObjectId(course_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail='Invalid course ID format')

    course = db.courses.find_one({'_id': ObjectId(course_id)}, {'_id':0,})
    if not course:
        raise HTTPException(status_code=404, detail='Course not found')
    chapters = course.get('chapters', [])
    try:
        chapter = chapters[int(chapter_id)]
    except(ValueError, IndexError) as e:
        raise HTTPException(status_code=404, detail='Chapter not found') from e
    return chapter





