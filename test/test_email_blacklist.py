import pytest

from .emailblacklist import EmailBlacklist


def test_email_blacklist():
    assert EmailBlacklist.is_ban("payprotec@yahoo.com") == True
    assert EmailBlacklist.is_ban("viktor.iy.ask.uchk.o.1.9.99@gmail.com") == True
    assert EmailBlacklist.is_ban("v.ikto.riyaskuc.h.k.o1999@gmail.com") == True
    assert EmailBlacklist.is_ban("vi.k.t.ori.y.askuchk.o.19.9.9@gmail.com") == True
    assert EmailBlacklist.is_ban("a.lek.sej.stuko.r.uk.o.v.2048@gmail.com") == True

