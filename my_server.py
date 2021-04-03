import asyncio
import re
import time as tm


metric = {}


class ClientServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None
        self.error = "error\nwrong command\n\n"
        self.put_data_pattern = r"[a-z._]+\s\d+\.?\d+?\s\d+"  # паттерн put зароса
        self.get_pattern = r"[a-z._]+"  # паттерн get запроса

    def connection_made(self, transport):
        self.transport = transport

    def put_validation(self, data: str):
        """
        Валидация полученных данных в запросе put
        :param data: полученные данные
        :return: ok в случае успешной валидации и error в противном случае
        """
        # print(f"data for pattern: {data}")
        if re.fullmatch(self.put_data_pattern, data):
            key, val, time = data.split()
            if key not in metric:
                metric[key] = []
                metric[key].append((float(val), time))
            else:
                for tup in metric[key]:
                    if tup[1] == time:
                        old_val = tup[0]
                        index = metric[key].index((old_val, time))
                        metric[key][index] = (float(val), time)
                        break
                else:
                    metric[key].append((float(val), time))
            return "ok\n\n"
        else:
            return self.error

    def get_validations(self, data):
        """
        Валидация полученных данных в запросе get
        :param data: полученные данные
        :return: формирование ответного сообщения в случае успешной валидации и error в противном случае
        """
        if re.fullmatch(self.get_pattern, data) or data == "*":
            response = "ok"
            if data == "*":
                for key in metric:
                    for information in metric[key]:
                        response += f"\n{key} {information[0]} {str(information[1])}"
            elif data in metric:
                for information in metric[data]:
                    response += f"\n{data} {information[0]} {str(information[1])}"
            else:
                pass
            response += "\n\n"
            return response
        else:
            return self.error

    def process_data(self, data: str):
        """
        Определение метода запроса и полученных данных
        :param data: полученные данные в запросе
        :return: None или error в случае неизвестного метода
        """
        if len(data.rstrip().split()) == 1:
            return self.error
        method, data = data.rstrip().split(" ", 1)
        # print(f"method: {method}, data: {data}.")
        if method not in ["put", "get"]:
            return self.error
        if method == "get":
            return self.get_validations(data)
        if method == "put":
            return self.put_validation(data)

    def data_received(self, data):
        """Этот метод вызывается когда будут приняты данные от клиента"""
        print(f"Data received: {data}. Time: {tm.time()}.")
        # обрабатываем принятые данные, формируем ответное сообщение
        if data == b"\n":
            self.transport.write(self.error.encode())
        else:
            response = self.process_data(data.decode())
            self.transport.write(response.encode())  # отправляем ответ
            # print(f"data sent: {response}.")


def run_server(host, port):
    """Запуск сервера"""
    loop = asyncio.get_event_loop()
    coroutine = loop.create_server(
        ClientServerProtocol,
        host, port
    )
    server = loop.run_until_complete(coroutine)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Сonnection interrupted!")
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == "__main__":
    run_server("127.0.0.1", 8889)
