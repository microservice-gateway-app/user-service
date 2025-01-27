import uvicorn
from fastapi import FastAPI

from users.config import UserServiceConfigurations
from users.module import provide_injector


injector = provide_injector()
app = injector.get(FastAPI)

if __name__ == "__main__":
    uvicorn.run(app, port=injector.get(UserServiceConfigurations).PORT)
