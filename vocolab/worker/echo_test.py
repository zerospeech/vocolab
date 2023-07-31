from vocolab.data import models
from vocolab.worker.server import echo

while True:
    msg = input("msg1: ")
    if msg == "quit":
        break
    slm = models.tasks.SimpleLogMessage(label="test-client", message=msg)
    echo.delay(slm.dict())
    print("submitted\nNext")

print("Quiting hyperloop")
print("bye.")
