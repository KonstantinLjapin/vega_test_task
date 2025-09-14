from contextlib import asynccontextmanager
from pathlib import Path

import mapscript
from typing import Union
import uvicorn
from sqlalchemy.orm import Session
from fastapi import FastAPI, Request, Response, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from src.dependencies import init_db, get_db, add_map_record


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при запуске
    init_db(db_path="sqlite:///maps.db", directory_path="static")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_item(request: Request):
    query_params = request.query_params
    print(query_params)
    return Response("param ok!", status_code=200)


@app.post("/upload")
async def upload_map_json_files(
    map_file: UploadFile = File(..., description="Файл с расширением .map"),
    json_file: UploadFile = File(..., description="Файл с расширением .json"),
    db: Session = Depends(get_db)
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

    mapname = Path(map_file.filename).stem

    try:
        # Пытаемся добавить запись в БД
        add_map_record(db, mapname, map_content.decode('utf-8'), json_content.decode('utf-8'))

        return JSONResponse(
            status_code=200,
            content={
                "message": "Файлы успешно загружены и сохранены в БД",
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
    except Exception as e:
        # В случае ошибки возвращаем ошибку
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка при сохранении в базу данных"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3007)
