from contextlib import contextmanager

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from src.models import Base, MapRecord
import os
from pathlib import Path
import tempfile

# Константа для временной директории
TEMP_DIR = os.path.join(tempfile.gettempdir(), 'map_data')


def add_map_record(session, mapname, mapstyle, gjson):
    """
    Добавляет новую запись о карте, если запись с таким mapname еще не существует.
    """
    # Проверяем, существует ли уже запись с таким mapname
    existing_record = session.query(MapRecord).filter_by(mapname=mapname).first()

    if existing_record:
        print(f"Запись с mapname '{mapname}' уже существует. Пропускаем добавление.")
        return existing_record
    else:
        new_map = MapRecord(mapname=mapname, mapstyle=mapstyle, gjson=gjson)
        session.add(new_map)
        session.commit()
        print(f"Запись с mapname '{mapname}' успешно добавлена.")
        return new_map


def find_map_json_pairs(directory):
    """
    Находит пары .map и .json файлов в указанной директории.
    """
    directory_path = Path(directory)
    map_files = list(directory_path.glob("*.map"))

    pairs = []
    for map_file in map_files:
        json_file = map_file.with_suffix(".json")
        if json_file.exists():
            pairs.append((map_file, json_file))
        else:
            print(f"Предупреждение: Для {map_file} не найден соответствующий .json файл")

    return pairs


def load_map_pairs_from_directory(session, directory_path: str):
    """
    Загружает пары .map и .json файлов из указанной директории в базу данных.
    """
    # Создаем временную директорию, если она не существует
    try:
        os.makedirs(TEMP_DIR, mode=0o755, exist_ok=True)
        print(f"Создана временная директория: {TEMP_DIR}")
    except PermissionError as e:
        print(f"Ошибка: Невозможно создать временную директорию {TEMP_DIR}. {e}")
        return

    # Находим пары файлов
    pairs = find_map_json_pairs(directory_path)

    if not pairs:
        print("Не найдено ни одной пары .map/.json файлов")
        return

    # Обрабатываем каждую пару
    for map_file, json_file in pairs:
        mapname = map_file.stem  # Имя без расширения

        # Проверяем, существует ли уже запись
        if session.query(MapRecord).filter_by(mapname=mapname).first():
            print(f"Запись '{mapname}' уже существует, пропускаем")
            continue

        try:
            # Читаем содержимое файлов (без модификации)
            map_content = map_file.read_text(encoding='utf-8')
            json_content = json_file.read_text(encoding='utf-8')

            # Добавляем запись в БД (без модификации .map файла)
            add_map_record(session, mapname, map_content, json_content)

        except Exception as e:
            print(f"Ошибка при обработке файлов {map_file}: {e}")


def init_db(db_path: str, directory_path: str):
    """
    Инициализирует подключение к базе данных, создает таблицы только если они не существуют,
    и заполняет бд данными.
    """
    print("init db.")
    engine = create_engine(db_path)

    # Проверяем, существуют ли таблицы в базе данных
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Создаем таблицы только если они не существуют
    if 'maps' not in existing_tables:
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Загружаем пары файлов из текущей директории
        load_map_pairs_from_directory(session, directory_path)

        # Выводим все записи для проверки
        all_records = session.query(MapRecord).all()
        print(f"\nВсего записей в базе: {len(all_records)}")

        session.close()
    else:
        print("Таблицы уже существуют.")


async def get_db():
    """
    Контекстный менеджер для получения сессии БД

    Yields:
        Session: Сессия базы данных
    """
    db_path = "sqlite:///maps.db" # при использовании переменных уходит в переменные проекта
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    # Инициализируем БД
    init_db(db_path="sqlite:///maps.db", directory_path="static")
