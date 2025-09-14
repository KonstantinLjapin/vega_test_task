import mapscript
from typing import Union
import uvicorn
from fastapi import FastAPI, Request, Response, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
app = FastAPI()


@app.get("/")
def read_item(request: Request):
    query_params = request.query_params
    print(query_params)
    return Response("param ok!", status_code=200)


@app.post("/upload")
async def upload_map_json_files(
    map_file: UploadFile = File(..., description="Файл с расширением .map"),
    json_file: UploadFile = File(..., description="Файл с расширением .json")
):
    # Проверяем расширения файлов
    if not map_file.filename.endswith('.map'):
        raise HTTPException(
            status_code=400,
            detail="Первый файл должен иметь расширение .map"
        )
    if not json_file.filename.endswith('.json'):
        raise HTTPException(
            status_code=400,
            detail="Второй файл должен иметь расширение .json"
        )

    # Содержимое файлов можно прочитать асинхронно
    map_content = await map_file.read()
    json_content = await json_file.read()

    with open(f"static/{map_file.filename}", "wb") as f:
        f.write(map_content)
    with open(f"static/{json_file.filename}", "wb") as f:
        f.write(json_content)

    # Возвращаем информацию о загруженных файлах
    return JSONResponse(
        status_code=200,
        content={
            "message": "Файлы успешно загружены",
            "map_file": {
                "filename": map_file.filename,
                "content_type": map_file.content_type,
                "size": len(map_content)
            },
            "json_file": {
                "filename": json_file.filename,
                "content_type": json_file.content_type,
                "size": len(json_content)
            }
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3007)
