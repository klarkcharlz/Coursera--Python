import socket
import time
from operator import itemgetter  # подключается для сортировки


class ClientError(Exception):
    """Класс ошибки клиента"""
    def __init__(self, text: str):
        self.text = text

    def __str__(self):
        return self.text


class Client:
    """Класс клиента"""
    def __init__(self, host: str, port: int, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        try:  # пробуем подключиться
            self.sock = socket.create_connection((host, port), timeout)
        # по условию задачи при возникновении каких либо ошибок в соединение мы должны выбрасывать своё исключение
        except socket.error:
            raise ClientError("no connection.")

    def put_validations(self):
        """Валидация сообщения полученного в ответ от сервера на запрос Put"""
        data = b""  # так как данные получаются в бинарном виде
        while not data.endswith(b"\n\n"):  # считываем пока не встретим признак конца ответного сообщения
            try:
                data += self.sock.recv(1024)
            except socket.error:
                raise ClientError("Connection problems.")
        data = data.decode()  # преобразуем в str
        if len(data) == 4 and data[0:2] == "ok":  # согласно условию
            return None
        else:
            raise ClientError("Server error")

    def put(self, metric: str, value, timestamp=None):
        """PUT запрос серверу"""
        if not timestamp:
            timestamp = int(time.time(1))
        try:
            self.sock.sendall(f"put {metric} {value} {timestamp}\n".encode("utf8"))  # put запрос
        except socket.error:
            raise ClientError("Connection problems.")
        else:  # приходится это выполнять так как по условию мы должны проводить валидацию ответа от сервера
            self.put_validations()  # если чтото не так с данными внутри функции выкинется исключение

    def validations(self) -> dict:
        """Валидация сообщения полученного в ответ от сервера на запрос Get"""
        data = b""  # так как данные получаются в бинарном виде
        while not data.endswith(b"\n\n"):  # считываем пока не встретим признак конца ответного сообщения
            try:
                data += self.sock.recv(1024)
            except socket.error:
                raise ClientError("Connection problems.")
        data = data.decode()  # преобразуем в str
        if len(data) == 4 and data[0:2] == "ok":  # согласно условию
            return {}
        status, data = data.split("\n", 1)
        data.rstrip().split("\n")
        if status not in ["ok", "error"]:
            raise ClientError("Close connection Error")
        if status == "error":
            raise ClientError("wrong command")
        try:
            # пытаемся пропарсить полученный ответ
            data_dict = {}
            for string in data.rstrip().split("\n"):
                metric, value, timestamp = string.split()
                if metric not in data_dict:
                    data_dict[metric] = []
                data_dict[metric].append((int(timestamp), float(value)))  # согласно условию
        except:
            raise ClientError("The received data is not valid")
        else:
            return data_dict

    def get(self, metric: str):
        """GET запрос серверу"""
        try:
            self.sock.sendall(f"get {metric}\n".encode("utf8"))  # get запрос
        except socket.error:
            raise ClientError("Connection problems.")
        else:
            data = self.validations()  # парсим ответ
            # если всё хорошо отсортируем списки из кортежей по ключу согласно условию
            for metric in data:
                if len(data[metric]) > 1:  # нет смысла сортировать если эллемент всего один
                    data[metric].sort(key=itemgetter(0))
            return data  # вовзращаем требуемый словарь

    def close(self):
        """Закрытие соединение"""
        # хоть по условию задачи и не требывалось, пригодится на будущее
        try:
            self.sock.close()
        except socket.error:
            raise ClientError("Close connection Error")

    def test(self):
        """создавался чисто для тестирования сервера на 6 неделе"""
        self.sock.sendall(b"\n")
        data = b""
        while not data.endswith(b"\n\n"):
            try:
                data += self.sock.recv(1024)
            except socket.error:
                raise ClientError("Connection problems.")
        data = data.decode()  # преобразуем в str
        print(data)


if __name__ == "__main__":
    client = Client("127.0.0.1", 8889, timeout=15)
    client.put("test_multivalue_key", 12.0, 1503319740)
    client.put("test_multivalue_key", 12.5, 1503319743)
    client.put("test_multivalue_key", 12.7, 1503319743)
    client.put("test_multivalue_key", 10.678, 1503319748)
    print(client.get("test_multivalue_key"))
    print(client.get("test_multivafdsfsdlue_key"))
    #client.test()
    client.close()
