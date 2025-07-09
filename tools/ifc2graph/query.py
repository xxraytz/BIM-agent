import mgclient
from llm_cypher import run_query

def run_cypher_query(memgraph_host, memgraph_port, query: str) -> str:
    """
    Выполняет Cypher-запрос в Memgraph и возвращает результат в виде строки.

    :param memgraph_host: адрес Memgraph, например '127.0.0.1'
    :param memgraph_port: порт Memgraph, например 7687
    :param query: строка с Cypher-запросом
    :return: строка с результатом (первой строки и колонки)
    """
    conn = mgclient.connect(host=memgraph_host, port=memgraph_port)
    cursor = conn.cursor()

    cursor.execute(query)
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result is None:
        return "Пустой результат"
    else:
        return str(result[0])

if __name__ == "__main__":
    query_text = run_query()
    print(query_text)
    response = run_cypher_query("127.0.0.1", 7687, query_text)
    print(f"Результат запроса: {response}")