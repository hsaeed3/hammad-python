"""hammad.data.models.pydantic.models.fast_model"""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Generic
from pydantic import BaseModel, ConfigDict
from dataclasses import dataclass
import copy

T = TypeVar("T")

__all__ = ("FastModel",)


class FastModel(BaseModel, Generic[T]):
    """
    FastModel = Pydantic BaseModel with IDE friendly(auto code completion),
    dot-accessible attributes with extended type hints & utilizing the
    Pydantic style `model_..` method naming convention to avoid conflicts.

    Combines the power of Pydantic BaseModel with dictionary-like access patterns.

    Examples:

        ```python
        model = FastModel(name="John", age=30)

        print(model.name)
        print(model.age)

        model.name = "Jane"
        print(model.name)

        model.age = 25

        # Dictionary-like access
        print(model["name"])
        model["age"] = 30
        ```
    """

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    def __init__(self: "FastModel[T]", *args: Any, **kwargs: Any) -> None:
        # Handle dictionary-like initialization
        if args and len(args) == 1 and isinstance(args[0], dict):
            kwargs.update(args[0])
            args = ()

        super().__init__(**kwargs)

        # Set all properties to None for annotated attributes not provided
        for k, v in self.model_attr_types().items():
            if k not in kwargs:
                setattr(self, k, None)

        # Set default values of annotated attributes
        self.init()

    def init(self: "FastModel[T]") -> None:
        """Override this method to set default values."""
        ...

    def __getstate__(self: "FastModel[T]") -> dict[str, Any]:
        return self.model_dump()

    def __setstate__(self: "FastModel[T]", state: dict[str, Any]) -> "FastModel[T]":
        return FastModel.model_from_dict(state)

    def __deepcopy__(
        self: "FastModel[T]", memo: Optional[dict[int, Any]] = None
    ) -> "FastModel[T]":
        # Get current field values
        current_data = {}
        for key in self.keys():
            current_data[key] = getattr(self, key)

        new = self.model_from_dict(current_data)
        for key in self.__class__.model_fields.keys():
            new.model_set_attribute(key, copy.deepcopy(getattr(self, key), memo=memo))
        return new

    # Dictionary-like access methods
    def __getitem__(self: "FastModel[T]", key: str) -> Any:
        """Get field value using dict-like access."""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __setitem__(self: "FastModel[T]", key: str, value: Any) -> None:
        """Set field value using dict-like access."""
        setattr(self, key, value)

    def __contains__(self: "FastModel[T]", key: str) -> bool:
        """Check if field exists using 'in' operator."""
        return hasattr(self, key) or key in self.__class__.model_fields

    def get(self: "FastModel[T]", key: str, default: Any = None) -> Any:
        """Get field value with optional default."""
        return getattr(self, key, default)

    def keys(self: "FastModel[T]"):
        """Return all field names."""
        return list(self.__class__.model_fields.keys()) + [
            k for k in self.__dict__.keys() if not k.startswith("_")
        ]

    def items(self: "FastModel[T]"):
        """Return all field (name, value) pairs."""
        for key in self.keys():
            yield key, getattr(self, key)

    def values(self: "FastModel[T]"):
        """Return all field values."""
        for key in self.keys():
            yield getattr(self, key)

    def update(self: "FastModel[T]", other: dict) -> None:
        """Update multiple fields at once."""
        for key, value in other.items():
            setattr(self, key, value)

    @classmethod
    def model_from_dict(cls: type["FastModel[T]"], d: dict[str, Any]) -> "FastModel[T]":
        return cls(**d)

    @classmethod
    def model_attr_has_default_value(cls: type["FastModel[T]"], attr_name: str) -> bool:
        return hasattr(cls, attr_name) and not callable(getattr(cls, attr_name))

    @classmethod
    def model_get_attr_default_value(cls: type["FastModel[T]"], attr_name: str) -> Any:
        if cls.model_attr_has_default_value(attr_name):
            return getattr(cls, attr_name)
        else:
            return None

    @classmethod
    def model_attr_type(cls: type["FastModel[T]"], attr_name: str) -> type:
        return cls.model_attr_types()[attr_name]

    @classmethod
    def model_attr_types(cls: type["FastModel[T]"]) -> dict[str, type]:
        return cls.__annotations__ if hasattr(cls, "__annotations__") else {}

    @classmethod
    def model_attr_names(cls: type["FastModel[T]"]) -> List[str]:
        """
        Returns annotated attribute names
        :return: List[str]
        """
        return [k for k, v in cls.model_attr_types().items()]

    @classmethod
    def model_has_attr(cls: type["FastModel[T]"], attr_name: str) -> bool:
        """
        Returns True if class have an annotated attribute
        :param attr_name: Attribute name
        :return: bool
        """
        return bool(cls.model_attr_types().get(attr_name))

    def model_set_default(self: "FastModel[T]", attr_name: str) -> None:
        if self.model_attr_has_default_value(attr_name):
            attr_default_value: Any = self.model_get_attr_default_value(attr_name)
            setattr(self, attr_name, attr_default_value)

    def model_get_constructor(
        self: "FastModel[T]", attr_name: str, value: Any
    ) -> Tuple[Optional[Callable[..., Any]], Optional[type]]:
        """
        This method is used for type conversion.
        FastModel uses this method to get the type of a value, then based on the
        value, it return a constructor. If the type of a value is 'float' then
        it returns 'float' since 'float' is also a constructor to build a float
        value.
        """
        attr_type1: type = self.model_attr_type(attr_name)
        constructor: Optional[Callable[..., Any]] = None
        element_type: Optional[type] = None

        if attr_type1 == float:
            constructor = float
        elif attr_type1 == str:
            constructor = str
        elif attr_type1 == int:
            constructor = int
        elif attr_type1 == list:
            constructor = list
        elif isinstance(value, FastModel):
            constructor = attr_type1.model_from_dict
        elif attr_type1 is Any:
            constructor = None
        elif isinstance(value, dict):
            if attr_type1 == dict:
                constructor = FastModel.model_from_dict
            elif issubclass(attr_type1, FastModel):
                constructor = self.model_attr_type(attr_name).model_from_dict
        elif attr_type1 is List:
            constructor = list
        elif hasattr(attr_type1, "__origin__"):
            if attr_type1.__dict__["__origin__"] is list:
                # if the type is 'List[something]'
                if len(attr_type1.__args__) == 0:
                    constructor = list
                elif len(attr_type1.__args__) == 1:
                    constructor = List
                    element_type = attr_type1.__args__[0]
                elif len(attr_type1.__args__) > 1:
                    raise TypeError("Only one dimensional List is supported")
            elif attr_type1.__dict__["__origin__"] is tuple:
                # if the type is 'Tuple[something]'
                constructor = tuple

        return constructor, element_type

    def model_set_attribute(self: "FastModel[T]", attr_name: str, value: Any) -> None:
        element_type: Optional[type] = None

        # Check for reserved dict keys (restored from original FastModel)
        dict_reserved_keys = vars(dict).keys()
        if attr_name in dict_reserved_keys:
            raise TypeError("You cannot set a reserved name as attribute")

        if self.model_has_attr(attr_name):
            if value is None:
                setattr(self, attr_name, None)
            elif self.model_attr_type(attr_name) == Any:
                setattr(self, attr_name, value)
            else:
                constructor, element_type = self.model_get_constructor(attr_name, value)
                if constructor is None:
                    setattr(self, attr_name, value)
                elif constructor == List:
                    # NOTE: fix typing
                    value_list: List[Any] = value
                    new_list: List[Any] = []

                    if element_type and issubclass(element_type, FastModel):
                        element_constructor: Callable[[Any], Any] = (
                            element_type.model_from_dict
                        )
                    else:
                        element_constructor = (
                            element_type if element_type else lambda x: x
                        )

                    for v in value_list:
                        new_list.append(element_constructor(v))
                    setattr(self, attr_name, new_list)
                elif constructor == list:
                    setattr(self, attr_name, list(value))
                else:
                    setattr(self, attr_name, constructor(value))
        else:
            if isinstance(value, dict):
                if isinstance(value, FastModel):
                    constructor: Callable[[Any], Any] = value.model_from_dict
                else:
                    constructor = FastModel.model_from_dict
                setattr(self, attr_name, constructor(value))
            else:
                setattr(self, attr_name, value)

    def model_set_attributes(self: "FastModel[T]", **d: Any) -> None:
        for k, v in d.items():
            self.model_set_attribute(k, v)

    def __getattr__(self: "FastModel[T]", item: str) -> T:
        """Handle missing attribute access like the original FastModel."""
        # Avoid infinite recursion by checking the actual object dict and model fields
        if item in self.__class__.model_fields or item in self.__dict__:
            return getattr(self, item)

        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute {item!r}"
        )

    def to_dict(
        self: "FastModel[T]",
        *args: Any,
        exclude: Optional[List[str]] = None,
        is_recursive: bool = False,
        exclude_none: bool = False,
        exclude_none_in_lists: bool = False,
        **kwargs: Any,
    ) -> dict[str, T]:
        """Convert to dictionary with various options."""
        exclude_set: Set[str] = set(exclude) if exclude is not None else set()
        ret: dict[str, T] = {}

        for k in self.keys():
            if k in exclude_set:
                continue

            v = getattr(self, k)

            if exclude_none and v is None:
                continue

            if is_recursive and isinstance(v, FastModel):
                ret[k] = v.to_dict(
                    is_recursive=is_recursive,
                    exclude_none=exclude_none,
                    exclude_none_in_lists=exclude_none_in_lists,
                )
            elif exclude_none_in_lists and isinstance(v, list):
                ret[k] = [
                    item.to_dict(exclude_none=True, is_recursive=is_recursive)
                    if isinstance(item, FastModel)
                    else item
                    for item in v
                ]
            else:
                ret[k] = v

        return ret

    def model_to_dataclass(self) -> dataclass:
        return dataclass(**self.model_dump())
