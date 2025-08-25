"""
Parse plan file line and return a list of (Book ID, Chapter num, [lines range])
If parser can't parse the plan line it returns None
"""
import re


class Parser:
    title_map = {
    }
    sep = ";"
    reg = None

    def __init__(self):
        self.books = set()
        self.chapters_cnt = 0

    def parse_item(self, line):
        """ Быт 1; Быт 2; Пс 1; Пс 2; Мф 1; Мф 2
            Лев 16; Пс 118:1-40; 2 Кор 12; 2 Кор 13
        """
        if self.sep not in line:
            return

        _line = line.strip()
        lt = []
        for ch in _line.split(self.sep):
            try:
                bn, _, num = ch.rpartition(" ")
            except IndexError:
                print(f"can't split by book and chapter: {_line}")
                raise

            lines = []
            try:
                ch_num, lines_range = num.split(":")
                num = ch_num
                try:
                    ls, le = lines_range.split("-")
                    lines.append(int(ls))
                    lines.append(int(le))
                except (IndexError, ValueError, TypeError) as err:
                    print(f"can't get lines range: {_line} - {err}")
                    raise

            except (IndexError, ValueError):
                # no lines range
                pass

            try:
                num = int(num)
            except (ValueError, TypeError):
                print(f"num is not integer: {_line}")
                raise

            book_name = bn.strip()
            lt.append((self.get_book_id(book_name), num, lines))
            self.books.add(book_name)
            self.chapters_cnt += 1
        return lt

    def get_book_id(self, book_name):
        try:
            return self.title_map[book_name]
        except KeyError:
            print(f"[ERROR] book '{book_name}' is not defined")
            raise

    def validate_title_map(self):
        """ validates title map to check it contains
        different books ids
        returns ids that don't exist
        """
        all_ids = set(range(1, 78))
        _ids = set()
        for k, v in self.title_map.items():
            if v in _ids:
                print(f"ERROR: duplicate id: {v}")
            _ids.add(v)
        return all_ids - _ids


class GeneralParser(Parser):
    title_map = {
        'Еккл': 24,
        'Ам': 37,
        'Ион': 39,
        'Мих': 40,
        '1 Тим': 72,
        'Иуд': 62,
        'Суд': 7,
        '2 Ин': 60,
        'Нав': 6,
        'Агг': 44,
        '1 Цар': 9,
        'Гал': 66,
        '4 Цар': 12,
        'Кол': 69,
        'Ис': 28,
        'Зах': 45,
        'Мк': 52,
        '1 Кор': 64,
        '2 Фес': 71,
        'Лев': 3,
        '2 Пар': 14,
        '1 Ин': 59,
        'Чис': 4,
        'Ин': 54,
        'Дан': 34,
        'Прит': 23,
        'Пс': 22,
        '1 Петр': 57,
        'Евр': 76,
        '1 Пар': 13,
        'Соф': 43,
        'Рим': 63,
        'Флм': 75,
        '3 Цар': 11,
        '3 Ин': 61,
        'Руфь': 8,
        'Плач': 30,
        'Езд': 15,
        'Исх': 2,
        'Неем': 16,
        'Мф': 51,
        'Фил': 68,
        'Иоил': 36,
        '2 Цар': 10,
        'Иак': 56,
        'Тит': 74,
        'Быт': 1,
        '2 Кор': 65,
        '1 Фес': 70,
        'Иез': 33,
        'Деян': 55,
        '2 Петр': 58,
        'Лк': 53,
        'Ос': 35,
        'Втор': 5,
        'Песн': 25,
        'Откр': 77,
        'Авд': 38,
        'Иов': 21,
        'Наум': 41,
        '2 Тим': 73,
        'Есф': 20,
        'Иер': 29,
        'Еф': 67,
        'Авв': 42,
        'Мал': 46,
    }

