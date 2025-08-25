"""
Parse plan file and return list of (Book ID, Chapter num, [lines range])
If parser can't parse the plan line it returns None
"""
import re

from .General import Parser


class ParseChapterException(Exception):
    pass


class AzbykaParser(Parser):
    """
    - books range always contains last chapter of the start range book
    - no lines ranges
    """
    title_map = {
        'Иона': 39,
        'Иуд': 62,
        'Еф': 67,
        'Лк': 53,
        'Нав': 6,
        'Наум': 41,
        'Мф': 51,
        'Ис': 28,
        'Мк': 52,
        'Вар': 32,
        'Притч': 23,
        'Иудифь': 19,
        'Мал': 46,
        'Гал': 66,
        'Соф': 43,
        'ПослИер': 31,
        '2Ин': 60,
        '1Ездр': 15,
        '1Цар': 9,
        'Лев': 3,
        'Руф': 8,
        'Флп': 68,
        'Зах': 45,
        '3Ин': 61,
        'Есф': 20,
        '1Петр': 57,
        'Кол': 69,
        'Плач': 30,
        '2Цар': 10,
        '4Цар': 12,
        'Иез': 33,
        'Тов': 18,
        'Числ': 4,
        'Сир': 27,
        'Агг': 44,
        'Неем': 16,
        'Ос': 35,
        '2Кор': 65,
        'Быт': 1,
        'Мих': 40,
        'Исх': 2,
        'Тит': 74,
        'Ам': 37,
        '1Макк': 47,
        'Флм': 75,
        '1Кор': 64,
        '2Фес': 71,
        '1Ин': 59,
        'Авв': 42,
        'Рим': 63,
        'Ин': 54,
        '2Тим': 73,
        'Иоиль': 36,
        '2Макк': 48,
        'Втор': 5,
        '1Фес': 70,
        'Песн': 25,
        '1Тим': 72,
        'Дан': 34,
        'Еккл': 24,
        'Прем': 26,
        '3Макк': 49,
        'Евр': 76,
        'Суд': 7,
        '2Петр': 58,
        'Откр': 77,
        '1Пар': 13,
        'Иов': 21,
        '2Пар': 14,
        'Пс': 22,
        'Иер': 29,
        'Иак': 56,
        '3Цар': 11,
        'Деян': 55,
        '2Ездр': 17,
     }

    def _parse_chapter(self, chapter):
        """ 1Пар.29
        """
        try:
            bk, num = chapter.split(".")
        except (IndexError, ValueError) as err:
            raise ParseChapterException(f"can't parse chapter '{chapter}': {err}")

        try:
            num = int(num)
        except (ValueError, TypeError):
            raise ParseChapterException(f"num is not integer: {chapter}")

        book_name = bk.strip()
        self.chapters_cnt += 1
        self.books.add(book_name)
        return (self.get_book_id(book_name), num, [])

    def parse_item(self, line):
        """
            1Пар.9-10; 2Кор.4; Пс.125
            1Пар.29-2Пар.1; Гал.1; Пс.135
            2Пар.36; Кол.3; Иов.2
        """
        if self.sep not in line:
            return

        _line = line.strip()
        lt = []
        for ch in _line.split(self.sep):
            try:
                sb, se = ch.split("-")
                ch_s = self._parse_chapter(sb)
                lt.append(ch_s)

                try:
                    ch_e = self._parse_chapter(se)
                    book_id = ch_e[0]
                    num_s = 1
                    num_e = ch_e[1]
                except ParseChapterException:
                    # not a chapter, but num
                    book_id = ch_s[0]
                    num_s = ch_s[1] + 1
                    try:
                        num_e = int(se)
                    except (ValueError, TypeError):
                        print(f"can't parse end range num: {_line}")
                        raise
                for _n in range(num_s, num_e+1):
                    lt.append((book_id, _n, []))
                    self.chapters_cnt += 1
            except (IndexError, ValueError):
                # no range
                ch_a = self._parse_chapter(ch)
                lt.append(ch_a)
        return lt

