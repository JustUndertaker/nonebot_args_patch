import abc
from collections import defaultdict
from typing import (
    Any,
    ItemsView,
    Iterator,
    KeysView,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Tuple,
    TypeVar,
    Union,
    ValuesView,
    overload,
)

from .args import Default

T = TypeVar("T")


class ArgsProvider(abc.ABC, MutableMapping[int, List[Default]]):
    """默认Args

    参数:
        args: 当前存储器中已有的Default args
    """

    @abc.abstractmethod
    def __init__(self, args: Mapping[int, List[Default]]):
        raise NotImplementedError


class DictProvider(defaultdict, ArgsProvider):
    def __init__(self, args: Mapping[int, List[Default]]):
        super().__init__(list, args)


class DefaultManager(MutableMapping[int, List[Default]]):
    """DefaultArg管理器

    实现了常用字典操作，用于管理DefaultArg。
    """

    def __init__(self):
        self.provider: DictProvider = DictProvider({})

    def __repr__(self) -> str:
        return f"ArgsManager(provider={self.provider!r})"

    def __contains__(self, o: object) -> bool:
        return o in self.provider

    def __iter__(self) -> Iterator[int]:
        return iter(self.provider)

    def __len__(self) -> int:
        return len(self.provider)

    def __getitem__(self, key: int) -> List[Default]:
        return self.provider[key]

    def __setitem__(self, key: int, value: List[Default]) -> None:
        self.provider[key] = value

    def __delitem__(self, key: int) -> None:
        del self.provider[key]

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, DefaultManager) and self.provider == other.provider

    def keys(self) -> KeysView[int]:
        return self.provider.keys()

    def values(self) -> ValuesView[List[Default]]:
        return self.provider.values()

    def items(self) -> ItemsView[int, List[Default]]:
        return self.provider.items()

    @overload
    def get(self, key: int) -> Optional[List[Default]]:
        ...

    @overload
    def get(self, key: int, default: T) -> Union[List[Default], T]:
        ...

    def get(
        self, key: int, default: Optional[T] = None
    ) -> Optional[Union[List[Default], T]]:
        return self.provider.get(key, default)

    def pop(self, key: int) -> List[Default]:
        return self.provider.pop(key)

    def popitem(self) -> Tuple[int, List[Default]]:
        return self.provider.popitem()

    def clear(self) -> None:
        self.provider.clear()

    def update(self, __m: MutableMapping[int, List[Default]]) -> None:
        self.provider.update(__m)

    def setdefault(self, key: int, default: List[Default]) -> List[Default]:
        return self.provider.setdefault(key, default)

    def get_arg(self) -> Default:
        """
        获取一个arg，根据priority依次返回
        """
        for priority in sorted(self.keys()):
            for result in self[priority]:
                yield result
