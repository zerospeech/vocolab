from zerospeech.db.models import tasks as model_task
from zerospeech.worker.server import echo

while True:
    msg = input("msg1: ")
    if msg == "quit":
        break
    slm = model_task.SimpleLogMessage(label="test-client", message=msg)
    echo.delay(slm.dict())
    print("submitted\nNext")

print("Quiting hyperloop")
print("bye.")
