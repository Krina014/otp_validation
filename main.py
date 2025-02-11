from fastapi import FastAPI
from routers import otp
from scheduler import scheduler
import uvicorn

app = FastAPI(
    title="OTP",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "persistAuthorization": True
    }
)


app.include_router(otp.router)


# Ensure scheduler stops when FastAPI app shuts down
@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)