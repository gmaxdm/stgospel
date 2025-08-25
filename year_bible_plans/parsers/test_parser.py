import pytest


from .General import GeneralParser


PARSER = [
    {
        "lines": [
            "Быт 1; Быт 2; Пс 1; Пс 2; Мф 1; Мф 2",
            "Лев 16; Пс 118:1-40; 2 Кор 12; 2 Кор 13",
        ],
        "res": [
            [
                (1, 1, []),
                (1, 2, []),
                (22, 1, []),
                (22, 2, []),
                (51, 1, []),
                (51, 2, []),
            ],
            [
                (3, 16, []),
                (22, 118, [1, 40]),
                (65, 12, []),
                (65, 13, []),
            ],
        ],
    },
]


@pytest.fixture(params=PARSER)
def testcase(request):
    return request.param


def test_parser(testcase):
    lines = testcase["lines"]
    parser = GeneralParser()
    for i, line in enumerate(lines):
        lt = parser.parse_item(line)
        res = testcase["res"][i]
        assert len(lt) == len(res)
        assert lt == res

