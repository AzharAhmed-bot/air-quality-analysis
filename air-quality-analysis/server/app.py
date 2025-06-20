from fastapi import FastAPI
import httpx
from fastapi.middleware.cors import CORSMiddleware



app=FastAPI()
origins = [
    "http://localhost:3000",  
    "http://127.0.0.1:3000",
    "*" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            
    allow_credentials=True,
    allow_methods=["*"],              
    allow_headers=["*"],              
)



@app.get('/locations')
async def get_locations():
    url='http://api.sensors.africa/v2/locations/'
    cookies = {
        "csrftoken": "SokQeIlq97mpRNlU65M6L3o",
        "sessionid": "hsoksd6rlabl80thzf3givz5rnkgpkrm"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, cookies=cookies)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch locations", "status_code": response.status_code}
    

@app.get('/now')
async def get_live_data():
    url='http://api.sensors.africa/v2/live/'
    cookies = {
        "csrftoken": "SokQeIlq97mpRNlU65M6L3o",
        "sessionid": "hsoksd6rlabl80thzf3givz5rnkgpkrm"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, cookies=cookies)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch live data", "status_code": response.status_code}
    

