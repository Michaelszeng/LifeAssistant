import modal

app = modal.App()

image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install("torch==2.2.1")
    # TODO: ADD OTHER PIP INSTALLS
)


@app.function(image=image, gpu="any")
@modal.web_endpoint(method="POST")
def square(item: dict):
    return {"square": item['x']**2}