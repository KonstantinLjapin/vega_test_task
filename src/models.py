from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class MapRecord(Base):
    """
    Класс для представления записи о карте в базе данных.

    """
    __tablename__ = 'maps'

    id = Column(Integer, primary_key=True, autoincrement=True)
    mapname = Column(String(100), unique=True, nullable=False, index=True)  # Уникальное имя карты с индексом
    mapstyle = Column(Text, nullable=False)  # Содержимое .map файла
    gjson = Column(Text, nullable=False)  # Содержимое .json файла (GeoJSON)

    def __repr__(self):
        return f"<MapRecord(mapname='{self.mapname}')>"
