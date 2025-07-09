import mgclient

def import_json_to_memgraph(host, port, json_path):
    # Подключаемся к Memgraph
    conn = mgclient.connect(host=host, port=port)
    cursor = conn.cursor()

    # Выполняем вызов процедуры импорта JSON
    query = f'CALL import_util.json("{json_path}");'
    
    try:
        cursor.execute(query)
        print(f"Файл {json_path} успешно импортирован в Memgraph.")
    except mgclient.DatabaseError as e:
        print(f"Ошибка при импорте: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Путь к JSON-файлу внутри контейнера Memgraph
    json_file_path = "/tmp/0705_183750_ifc.json"  # замените на актуальный путь внутри контейнера

    import_json_to_memgraph("127.0.0.1", 7687, json_file_path)
