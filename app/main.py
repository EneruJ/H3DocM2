from fastapi import FastAPI, HTTPException
import aioredis
import memcache 

app = FastAPI()

async def connect_to_redis():
    redis = await aioredis.create_redis_pool("redis://localhost:6379")
    return redis

@app.on_event("startup")
async def startup_event():
    app.redis = await connect_to_redis()

@app.on_event("shutdown")
async def shutdown_event():
    app.redis.close()
    await app.redis.wait_closed()

memcached = memcache.Client(["memcached:11211"])

@app.get("/")
async def read_root():
    try:
        value = memcached.get("nb_click")
        
        if value is None:
            value = await app.redis.get("nb_click") or 0
            memcached.set("nb_click", value, time=3600)  
        
        await app.redis.set("nb_click", int(value) + 1)
        result = await app.redis.get("nb_click")
        return {"Nombre d'entrées": int(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur Redis")

@app.post("/reset")
async def reset_counter():
    try:
        await app.redis.set("nb_click", 0)
        memcached.set("nb_click", 0, time=3600)
        return {"Message": "Le compteur a été réinitialisé avec succès."}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur Redis")
