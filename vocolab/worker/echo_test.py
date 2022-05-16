from vocolab.db.models import tasks as model_task
from vocolab.worker.server import echo

while True:
    msg = input("msg1: ")
    if msg == "quit":
        break
    slm = model_task.SimpleLogMessage(label="test-client", message=msg)
    echo.delay(slm.dict())
    print("submitted\nNext")

print("Quiting hyperloop")
print("bye.")
