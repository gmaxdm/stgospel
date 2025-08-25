import pytest


from .Azbyka import AzbykaParser


AZBYKA = [
    {
        "lines": [
            "1Пар.9-10; 2Кор.4; Пс.125",
            "1Пар.29-2Пар.1; Гал.1; Пс.135",
            "2Пар.36; Кол.3; Иов.2",
        ],
        "res": [
            [
                (13, 9, []),
                (13, 10, []),
                (65, 4, []),
                (22, 125, []),
            ],
            [
                (13, 29, []),
                (14, 1, []),
                (66, 1, []),
                (22, 135, []),
            ],
            [
                (14, 36, []),
                (69, 3, []),
                (21, 2, []),
            ],
        ],
    },
]


@pytest.fixture(params=AZBYKA)
def test_azbyka_case(request):
    return request.param


def test_azbyka(test_azbyka_case):
    lines = test_azbyka_case["lines"]
    parser = AzbykaParser()
    for i, line in enumerate(lines):
        lt = parser.parse_item(line)
        res = test_azbyka_case["res"][i]
        assert len(lt) == len(res)
        assert lt == res

