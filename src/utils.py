import mapscript
import re


class MapServer:
    def __init__(self, map_style: str):
        self.mapscript_obj = mapscript.fromstring(map_style)

    def process_request(self, query_string: str):
        request = mapscript.OWSRequest()
        mapscript.msIO_installStdoutToBuffer()
        request.loadParamsFromURL(query_string)
        status_id = self.mapscript_obj.OWSDispatch(request)
        content_type = mapscript.msIO_stripStdoutBufferContentType()
        result = mapscript.msIO_getStdoutBufferBytes()
        mapscript.msIO_resetHandlers()

        status = 200 if status_id == mapscript.MS_SUCCESS else 400
        return status, content_type, result


def modify_map_style(map_content, json_full_path):
    """
    Модифицирует содержимое .map файла, заменяя путь к JSON файлу на абсолютный путь.

    Args:
        map_content (str): Исходное содержимое .map файла
        json_full_path (str): Полный абсолютный путь к JSON файлу

    Returns:
        str: Модифицированное содержимое .map файла
    """
    # Заменяем все найденные пути в CONNECTION на новый абсолютный путь
    pattern = r'CONNECTION\s+"[^"]*"'
    replacement = f'CONNECTION "{json_full_path}"'

    modified_content = re.sub(pattern, replacement, map_content)
    return modified_content
