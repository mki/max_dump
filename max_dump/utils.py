# pylint: disable=invalid-name
"""Small functions, objects and constants used by various modules.
"""
import io
import logging
import operator
import string
import textwrap
from itertools import chain
from typing import Dict, Iterable, Hashable, Union, List
from collections import defaultdict
from struct import unpack, calcsize


SHORT_S = calcsize('h')         # 16
INT_S = calcsize('i')           # 32
LONG_LONG_S = calcsize('q')     # 64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('max_dump')

DictOfDicts = Dict[Hashable, Dict]
DictOfList = Dict[Hashable, List]
DictOrValue = Union[Dict, Hashable]


def read_short(stream: io.BytesIO) -> int:
    """Read signed short integer (usually 16 bit).
    """
    return unpack('h', stream.read(SHORT_S))[0]


def read_int(stream: io.BytesIO) -> int:
    """Read signed integer (usually 32 bit).
    """
    return unpack('i', stream.read(INT_S))[0]


def read_long_long(stream: io.BytesIO) -> int:
    """Read signed integer (usually 64 bit).
    """
    return unpack('q', stream.read(LONG_LONG_S))[0]


def unset_sign_bit(number: int, length: int) -> int:
    """Unset sign bit from a `number'.

    `length' is the size of the number in bytes.
    """
    number_of_bits = length * 8
    # 8bit: 0b1000_0000 = 0x80
    # 32bit: 0x80_00_00_00
    sign_bit = 1 << (number_of_bits - 1)
    # 8bit: 0b1111_1111 = 0xFF
    # 32bit: 0xFF_FF_FF_FF
    byte_mask = (1 << number_of_bits) - 1
    # unset sign bit and keep length under int size
    number &= ~sign_bit & byte_mask
    # 8bit: ~sign_bit = 0b0111_1111
    return number


def _new_key(entry: DictOrValue, key: str) -> Hashable:
    new_key = None
    for sub_key in key.split('__'):
        assert isinstance(entry, Dict)
        new_key = entry[sub_key]
        entry = entry[sub_key]

    assert isinstance(new_key, Hashable)
    return new_key


def index_by(iterable: Iterable[DictOfDicts], key: str) -> DictOfDicts:
    """Return a dictionary from the given iterable.

    `key' may be nested like that: 'header__idn'
    """
    indexed = {}
    for entry in iterable:
        new_key = _new_key(entry, key)
        indexed[new_key] = entry
    return indexed


def group_by(iterable: List[DictOfDicts], key: str) -> DictOfList:
    """Group dictinaries in the iterable by key.
    """
    grouped: DictOfList = defaultdict(list)
    for entry in iterable:
        new_key = _new_key(entry, key)
        grouped[new_key].append(entry)
    return grouped


def bin2ascii(value_bytes):
    s = value_bytes.decode('ascii', 'replace')
    return ''.join(map(lambda x: x if x in string.printable else '.', s))


def slots(klass: type) -> Iterable:
    """Collect all slots from `klass' and its parents.
    """
    return chain.from_iterable(getattr(cls, '__slots__', [])
                               for cls in klass.__mro__)


class SimpleEqualityMixin:
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return vars(other) == vars(self)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class UCStringDecodedMixin:
    def __init__(self, *args, decoded: str = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.decoded = decoded

    @property
    def _props(self):
        decoded = f"decoded: {self.decoded}"
        return [decoded]

    @classmethod
    def _decode(cls, *args, st_base=None, **kwargs):
        return super()._decode(
                *args,
                st_base=st_base,
                decoded=st_base.value.decode('utf-16'),
                **kwargs
        )


class ReprMixin:
    def __repr__(self):
        class_name = self.__class__.__name__
        format_s = f"[{class_name}]"
        props = self._props
        props_s = '\n'.join(textwrap.indent(str(prop), " " * 4)
                            for prop in props)
        return f"\n{format_s}\n{props_s}\n"


class RawValueMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._raw: bytes = None

    @classmethod
    def _decode(cls, *args, st_base=None, **kwargs):
        inst = super()._decode(*args, st_base=st_base, **kwargs)
        inst._raw = st_base._raw
        return inst

class DecodeBaseMixin:
    @classmethod
    def _decode(cls, *args, **kwargs):
        if 'st_base' in kwargs:
            del kwargs['st_base']
        return cls(*args, **kwargs)
