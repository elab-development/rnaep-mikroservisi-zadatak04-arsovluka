from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis_om import HashModel, NotFoundError
import httpx
import asyncio
import os
from database import redis
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    INVENTORY_SERVICE_URL: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

app = FastAPI(title="Order Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods=['*'],
    allow_headers=['*']
)

class Order(HashModel, index=True):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str

    class Meta:
        database = redis

@app.get('/orders/{pk}')
async def get_order(pk: str):
    try:
        return Order.get(pk)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Order not found")

@app.post('/orders')
async def create_order(body: dict, background_tasks: BackgroundTasks):
    # Asinhroni poziv ka Inventory servisu - SADA KORISTI .env VARIJABLU
    async with httpx.AsyncClient() as client:
        response = await client.get(f'{settings.INVENTORY_SERVICE_URL}/products/{body["id"]}')
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Product not found in Inventory")
        product = response.json()

    order = Order(
        product_id=body['id'],
        price=product['price'],
        fee=0.2 * product['price'],
        total=1.2 * product['price'] * body['quantity'],
        quantity=body['quantity'],
        status='pending'
    )
    order.save()

    # Pokretanje pozadinskog zadatka
    background_tasks.add_task(process_order, order)

    return order

async def process_order(order: Order):
    # Simulacija obrade plaćanja (5 sekundi)
    await asyncio.sleep(5) 
    order.status = 'completed'
    order.save()
    
    # Slanje događaja u Redis Stream za Inventory servis
    redis.xadd('order_completed', order.model_dump(), '*')