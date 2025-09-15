from contextlib import asynccontextmanager
import json
import uvicorn
from sqlalchemy.orm import Session
from fastapi import FastAPI, Request, Response, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from src.dependencies import init_db, get_db, add_map_record, find_map_by_basename
from src.utils import MapServer, modify_map_style
import os
from pathlib import Path
import time

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при запуске
    init_db(directory_path="static")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/{map_name}")
async def read_item(request: Request, map_name: str, db=Depends(get_db)):
    # Получаем параметры запроса
    query_string = str(request.url.query)

    # Получаем данные из базы
    q = find_map_by_basename(db=db, filename=map_name)
    # TODO если знать больше о формате map_style можно более коректно сохранять файлы , ускорить работу можно не вызывая
    #  работу map_server а используя его процесс также нужно понять почему иногда идут от него ошибки в логах
    cache_dir = Path(os.getcwd()) / "cache"
    cache_dir.mkdir(exist_ok=True)
    temp_file_path = os.path.join(cache_dir, f"{map_name}.json")
    with open(temp_file_path, 'w', encoding='utf-8') as f:
            data = json.loads(q.gjson)
            json.dump(data, f, indent=4, ensure_ascii=False)
    try:
        # Модифицируем стиль карты
        mod_map_style = modify_map_style(map_content=q.mapstyle, json_full_path=temp_file_path)

        # Создаем обработчик карты
        map_server = MapServer(mod_map_style)

        # Обрабатываем запрос
        status, content_type, result = map_server.process_request(query_string)

        return Response(content=result, media_type=content_type, status_code=status)

    finally:
        # Удаляем временный файл
        if os.path.exists(temp_file_path):
            time.sleep(30)
            os.unlink(temp_file_path)


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
