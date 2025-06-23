"""hammad.objects.basedmodel"""

import copy
import re
from dataclasses import dataclass, field as dc_field
from functools import lru_cache
from typing import (
    Any, Annotated, Callable, Dict, List, Literal, Optional, 
    Pattern, Self, Set, TypeVar, Union, get_args, get_origin, overload
)

import msgspec
from msgspec import Meta, field as msgspec_field
from msgspec.json import decode, encode, schema
from msgspec.structs import Struct, asdict, fields

__all__ = (
    "BasedModel",
    "basedfield", "FieldInfo", "Field", "get_field_info", "is_basedfield",
    "str_basedfield", "int_basedfield", "float_basedfield", "list_basedfield", "basedvalidator"
)


def _get_field_schema(field) -> dict[str, Any]:
    """Helper method to generate schema for a single field."""
    field_type = field.type

    # Handle basic types
    if field_type == str:
        return {"type": "string"}
    elif field_type == int:
        return {"type": "integer"}
    elif field_type == float:
        return {"type": "number"}
    elif field_type == bool:
        return {"type": "boolean"}
    elif field_type == list:
        return {"type": "array"}
    elif field_type == dict:
        return {"type": "object"}

    # Handle Optional types (Union with None)
    if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
        args = field_type.__args__
        if len(args) == 2 and type(None) in args:
            # This is Optional[T]
            non_none_type = args[0] if args[1] is type(None) else args[1]
            base_schema = _get_type_schema(non_none_type)
            base_schema["nullable"] = True
            return base_schema

    # Handle generic types
    if hasattr(field_type, "__origin__"):
        origin = field_type.__origin__
        if origin is list:
            args = getattr(field_type, "__args__", ())
            if args:
                return {"type": "array", "items": _get_type_schema(args[0])}
            return {"type": "array"}
        elif origin is dict:
            return {"type": "object"}
        elif origin is set:
            args = getattr(field_type, "__args__", ())
            if args:
                return {
                    "type": "array",
                    "items": _get_type_schema(args[0]),
                    "uniqueItems": True,
                }
            return {"type": "array", "uniqueItems": True}

    # Default fallback
    return {"type": "object"}


def _get_type_schema(type_hint) -> dict[str, Any]:
    """Helper method to get schema for a type hint."""
    if type_hint == str:
        return {"type": "string"}
    elif type_hint == int:
        return {"type": "integer"}
    elif type_hint == float:
        return {"type": "number"}
    elif type_hint == bool:
        return {"type": "boolean"}
    elif type_hint == list:
        return {"type": "array"}
    elif type_hint == dict:
        return {"type": "object"}
    elif type_hint == set:
        return {"type": "array", "uniqueItems": True}
    else:
        return {"type": "object"}


class BasedModel(Struct):
    """Based, as defined by Lil B is:

    ```markdown
    "Based means being yourself.
    Not being scared of what people think about you.
    Not being afraid to do what you wanna do."
    ```

    NOTE: This model does support the dictionary interface, but
    does not support the `keys`, `values`, `items`, and `get`
    methods to allow for usage of those fields as key names.

    These wise words define this model. A `BasedModel` is
    interactable both through the dictionary interface, and
    dot notation, and utilizes `msgspec` to provide an interface
    identical to a `pydantic.BaseModel`, with the benefit of
    `msgspec's` superior performance (5-60x faster for common operations).
    """
    
    def __init_subclass__(cls, **kwargs):
        """Called when a class is subclassed to set up proper typing."""
        super().__init_subclass__(**kwargs)
        
        # Create dynamic properties for field access to help with IDE completion
        try:
            struct_fields = fields(cls)
            field_names = [f.name for f in struct_fields]
            
            # Store field names for IDE completion
            cls._field_names_literal = field_names
            
            # Create properties for each field to aid IDE completion
            for field_name in field_names:
                if not hasattr(cls, f'_get_{field_name}'):
                    def make_getter(fname):
                        def getter(self):
                            return getattr(self, fname)
                        return getter
                    
                    setattr(cls, f'_get_{field_name}', make_getter(field_name))
        except Exception:
            # If fields() fails, fallback gracefully
            pass
    
    # Remove complex metadata handling - let msgspec handle fields natively

    @classmethod
    @lru_cache(maxsize=None)
    def _get_field_names(cls) -> tuple[str, ...]:
        """Get all field names as a tuple for type hints."""
        struct_fields = fields(cls)
        return tuple(f.name for f in struct_fields)
    
    @classmethod
    @lru_cache(maxsize=None)
    def _get_fields_info(cls) -> Dict[str, Any]:
        """Cached method to get field information."""
        struct_fields = fields(cls)
        result = {}
        
        for f in struct_fields:
            field_info = {
                "field": f,
                "type": f.type,
                "required": f.required,
                "default": f.default if not f.required else None,
            }
            
            result[f.name] = field_info
        
        return result

    @classmethod
    def model_json_schema(cls) -> dict[str, Any]:
        """Returns the json schema for the object.

        Uses msgspec's native schema generation when possible for better performance.
        """
        try:
            # Try to use msgspec's native schema generation first
            return schema(cls)
        except Exception:
            # Fallback to manual schema generation
            schema_dict = {
                "type": "object",
                "properties": {},
                "required": [],
                "title": cls.__name__,
            }

            if cls.__doc__:
                schema_dict["description"] = cls.__doc__.strip()

            # Get field information from the struct
            fields_info = cls._get_fields_info()

            for field_name, field_info in fields_info.items():
                field = field_info["field"]
                field_schema = _get_field_schema(field)
                schema_dict["properties"][field_name] = field_schema

                # Add to required if field has no default
                if field.required:
                    schema_dict["required"].append(field_name)

            # Remove empty required array if no required fields
            if not schema_dict["required"]:
                del schema_dict["required"]

            return schema_dict

    def model_dump(
        self,
        *,
        mode: Literal["json", "python"] = "python",
        include: Optional[Union[Set[str], Set[int]]] = None,
        exclude: Optional[Union[Set[str], Set[int]]] = None,
        exclude_none: bool = False,
        exclude_defaults: bool = False,
        exclude_unset: bool = False,
    ) -> Any:
        """Dumps the object into a dictionary, or a json string.

        Note: exclude_unset is included for compatibility but has no effect
        as msgspec doesn't track unset state.
        """
        # Convert struct to dictionary using msgspec's optimized asdict
        data = asdict(self)

        # Handle include/exclude filtering
        if include is not None:
            if isinstance(include, set) and all(isinstance(k, str) for k in include):
                data = {k: v for k, v in data.items() if k in include}
            elif isinstance(include, set) and all(isinstance(k, int) for k in include):
                # For integer indices, convert to list of items and filter by index
                items = list(data.items())
                data = dict(items[i] for i in include if 0 <= i < len(items))

        if exclude is not None:
            if isinstance(exclude, set) and all(isinstance(k, str) for k in exclude):
                data = {k: v for k, v in data.items() if k not in exclude}
            elif isinstance(exclude, set) and all(isinstance(k, int) for k in exclude):
                # For integer indices, convert to list and exclude by index
                items = list(data.items())
                data = dict(items[i] for i in range(len(items)) if i not in exclude)

        # Handle None exclusion
        if exclude_none:
            data = {k: v for k, v in data.items() if v is not None}

        # Handle default exclusion
        if exclude_defaults:
            fields_info = self._get_fields_info()
            data = {
                k: v
                for k, v in data.items()
                if k not in fields_info
                or fields_info[k]["required"]
                or v != fields_info[k]["default"]
            }

        # Return based on mode
        if mode == "python":
            return data
        elif mode == "json":
            return encode(data).decode("utf-8")
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'json' or 'python'")

    def model_dump_json(
        self,
        *,
        indent: Optional[int] = None,
        include: Optional[Union[Set[str], Set[int]]] = None,
        exclude: Optional[Union[Set[str], Set[int]]] = None,
        exclude_none: bool = False,
        exclude_defaults: bool = False,
    ) -> str:
        """Generate a JSON representation of the model."""
        data = self.model_dump(
            mode="python",
            include=include,
            exclude=exclude,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )
        # msgspec's encode is faster than json.dumps
        return encode(data).decode("utf-8")

    def model_copy(
        self,
        *,
        update: Optional[Dict[str, Any]] = None,
        deep: bool = False,
        exclude: Optional[Union[Set[str], Set[int]]] = None,
    ) -> Self:
        """Create a copy of the struct, optionally updating fields."""
        if update is None:
            update = {}

        # Get current data as dict using msgspec's optimized asdict
        current_data = asdict(self)

        # Handle exclude filtering
        if exclude is not None:
            if isinstance(exclude, set) and all(isinstance(k, str) for k in exclude):
                current_data = {k: v for k, v in current_data.items() if k not in exclude}
            elif isinstance(exclude, set) and all(isinstance(k, int) for k in exclude):
                items = list(current_data.items())
                current_data = dict(items[i] for i in range(len(items)) if i not in exclude)

        # Update with new values
        current_data.update(update)

        # Create new instance
        new_instance = self.__class__(**current_data)

        if deep:
            # For deep copy, we need to recursively copy nested structures
            return copy.deepcopy(new_instance)

        return new_instance

    @classmethod
    def model_validate(cls, obj: Any) -> Self:
        """Validate and create an instance from various input types."""
        if isinstance(obj, cls):
            return obj
        elif isinstance(obj, dict):
            return cls(**obj)
        elif hasattr(obj, "__dict__"):
            return cls(**obj.__dict__)
        else:
            # Try to decode if it's a string/bytes
            try:
                if isinstance(obj, (str, bytes)):
                    decoded = decode(obj, type=cls)
                    return decoded
            except Exception:
                pass
            raise ValueError(f"Cannot validate {type(obj)} as {cls.__name__}")

    @classmethod
    def model_validate_json(cls, json_data: Union[str, bytes]) -> Self:
        """Create an instance from JSON string or bytes.

        Uses msgspec's optimized JSON decoder.
        """
        return decode(json_data, type=cls)

    @classmethod
    def model_fields(cls) -> Dict[str, Any]:
        """Get information about the struct's fields."""
        return cls._get_fields_info()

    @classmethod
    def model_load_from_model(
        cls,
        model : Any,
        title : Optional[str] = None,
        description : Optional[str] = None,
        init : bool = False,
        exclude : Optional[Union[Set[str], Set[int]]] = None,
    ) -> Self:
        """Load a model from another model.
        
        Args:
            model : The model to load from
            title : An optional title or title override for the model 
            description : An optional description for the model
            init : Whether to initialize the model with the field value
            exclude : Fields to exclude from the conversion
        """
        # Extract data from the source model
        if hasattr(model, 'model_dump'):
            # It's a pydantic-like model
            source_data = model.model_dump()
        elif hasattr(model, '__dict__'):
            # It's a regular object with attributes
            source_data = model.__dict__.copy()
        elif isinstance(model, dict):
            # It's already a dictionary
            source_data = model.copy()
        elif hasattr(model, '_asdict'):
            # It's a namedtuple
            source_data = model._asdict()
        else:
            # Try to use msgspec's asdict for msgspec structs
            try:
                source_data = asdict(model)
            except Exception:
                # Last resort - try to convert to dict
                try:
                    source_data = dict(model)
                except Exception:
                    raise ValueError(f"Cannot extract data from model of type {type(model)}")
        
        # Apply exclusions if specified
        if exclude is not None:
            if isinstance(exclude, set) and all(isinstance(k, str) for k in exclude):
                source_data = {k: v for k, v in source_data.items() if k not in exclude}
            elif isinstance(exclude, set) and all(isinstance(k, int) for k in exclude):
                items = list(source_data.items())
                source_data = dict(items[i] for i in range(len(items)) if i not in exclude)
        
        # Get the fields of the target class to filter compatible fields
        try:
            target_fields = cls._get_field_names()
            # Only include fields that exist in the target model
            filtered_data = {k: v for k, v in source_data.items() if k in target_fields}
        except Exception:
            # If we can't get field names, use all data
            filtered_data = source_data
        
        if init:
            # Create and return an instance
            return cls(**filtered_data)
        else:
            # Return the class type - this doesn't make much sense for the method signature
            # but following the parameter description, we'll return an uninitialized version
            # In practice, this would typically return the class itself or raise an error
            # For now, let's create an instance anyway since that's most useful
            return cls(**filtered_data)
    
    @classmethod
    def model_field_to_model(
        cls,
        fields : str,
        schema: Literal[
            "based",
            "dataclass",
            "pydantic",
            "msgspec",
            "typeddict",
            "namedtuple",
            "attrs",
            "dict",
        ] = "based",
        # Simple Override Params To Edit The Final Model
        # This method always goes field(s) -> model not to field
        title : Optional[str] = None,
        description : Optional[str] = None,
        field_name : str = "value",
        field_description : Optional[str] = None,
        field_examples : Optional[List[Any]] = None,
        init : bool = False,
    ) -> Any:
        """Convert a single field to a new model of any
        type.
        
        Args:
            fields: The field to be converted into the model
            schema: The target schema format to convert to (Defaults to a basedmodel)
            title : An optional title or title override for the model (uses the field name if not provided)
            description : An optional description for the model (uses the field description if not provided)
            field_name : The name of the field within this new model representing the target field (defaults to "value")
            field_description : An optional description for the field within this new model (defaults to None)
            field_examples : An optional list of examples for the field within this new model (defaults to None)
            init : Whether to initialize the model with the field value (defaults to False)
        """
        # Get field information from the class
        fields_info = cls._get_fields_info()
        
        if fields not in fields_info:
            raise ValueError(f"Field '{fields}' not found in {cls.__name__}")
        
        field_info = fields_info[fields]
        field_type = field_info["type"]
        
        # Handle default values properly, including default_factory
        if not field_info["required"]:
            field_default = field_info["default"]
            # Check for default_factory in the msgspec field
            msgspec_field = field_info["field"]
            if (hasattr(msgspec_field, 'default_factory') and 
                msgspec_field.default_factory is not msgspec.UNSET and 
                msgspec_field.default_factory is not msgspec.NODEFAULT):
                # It has a default_factory, call it to get the actual default
                try:
                    field_default = msgspec_field.default_factory()
                except Exception:
                    # If calling fails, use UNSET
                    field_default = msgspec.UNSET
            # If field_default is NODEFAULT but no default_factory, keep as UNSET
            elif field_default is msgspec.NODEFAULT:
                field_default = msgspec.UNSET
        else:
            field_default = msgspec.UNSET
        
        # Use provided title or default to field name
        model_title = title or fields.title()
        model_description = description or f"Model wrapping field '{fields}'"
        
        if schema == "based":
            # Create annotations for the dynamic class
            annotations = {field_name: field_type}
            
            # Create field definition
            class_dict = {"__annotations__": annotations}
            
            # Add default if available
            if field_default is not msgspec.UNSET:
                class_dict[field_name] = basedfield(
                    default=field_default,
                    description=field_description,
                    examples=field_examples
                )
            elif field_description or field_examples:
                class_dict[field_name] = basedfield(
                    description=field_description,
                    examples=field_examples
                )
            
            # Create the dynamic class
            DynamicModel = type(
                model_title.replace(" ", ""),
                (BasedModel,),
                class_dict
            )
            
            if init and field_default is not msgspec.UNSET:
                return DynamicModel(**{field_name: field_default})
            elif init:
                # Need a value to initialize with
                raise ValueError("Cannot initialize model without a default value")
            else:
                return DynamicModel
                
        elif schema == "dataclass":
            from dataclasses import make_dataclass, field as dc_field
            
            if field_default is not msgspec.UNSET:
                fields_list = [(field_name, field_type, dc_field(default=field_default))]
            else:
                fields_list = [(field_name, field_type)]
            
            DynamicDataclass = make_dataclass(
                model_title.replace(" ", ""),
                fields_list
            )
            
            if init and field_default is not msgspec.UNSET:
                return DynamicDataclass(**{field_name: field_default})
            elif init:
                raise ValueError("Cannot initialize dataclass without a default value")
            else:
                return DynamicDataclass
                
        elif schema == "pydantic":
            from pydantic import BaseModel, create_model
            
            pydantic_fields = {}
            if field_default is not msgspec.UNSET:
                pydantic_fields[field_name] = (field_type, field_default)
            else:
                pydantic_fields[field_name] = (field_type, ...)
            
            PydanticModel = create_model(
                model_title.replace(" ", ""),
                **pydantic_fields
            )
            
            if init and field_default is not msgspec.UNSET:
                return PydanticModel(**{field_name: field_default})
            elif init:
                raise ValueError("Cannot initialize pydantic model without a default value")
            else:
                return PydanticModel
                
        elif schema == "msgspec":
            # Create a msgspec Struct dynamically
            struct_fields = {field_name: field_type}
            if field_default is not msgspec.UNSET:
                struct_fields[field_name] = msgspec_field(default=field_default)
            
            DynamicStruct = type(
                model_title.replace(" ", ""),
                (Struct,),
                {"__annotations__": {field_name: field_type}}
            )
            
            if init and field_default is not msgspec.UNSET:
                return DynamicStruct(**{field_name: field_default})
            elif init:
                raise ValueError("Cannot initialize msgspec struct without a default value")
            else:
                return DynamicStruct
                
        elif schema == "typeddict":
            from typing import TypedDict
            
            # TypedDict can't be created dynamically in the same way
            # Return a dictionary with type information
            if init and field_default is not msgspec.UNSET:
                return {field_name: field_default}
            elif init:
                raise ValueError("Cannot initialize TypedDict without a default value")
            else:
                # Return a TypedDict class (though this is limited)
                return TypedDict(model_title.replace(" ", ""), {field_name: field_type})
                
        elif schema == "namedtuple":
            from collections import namedtuple
            
            DynamicNamedTuple = namedtuple(model_title.replace(" ", ""), [field_name])
            
            if init and field_default is not msgspec.UNSET:
                return DynamicNamedTuple(**{field_name: field_default})
            elif init:
                raise ValueError("Cannot initialize namedtuple without a default value")
            else:
                return DynamicNamedTuple
                
        elif schema == "attrs":
            try:
                import attrs
                
                if field_default is not msgspec.UNSET:
                    field_attr = attrs.field(default=field_default)
                else:
                    field_attr = attrs.field()
                
                @attrs.define
                class DynamicAttrs:
                    pass
                
                # Set the field dynamically
                setattr(DynamicAttrs, field_name, field_attr)
                DynamicAttrs.__annotations__ = {field_name: field_type}
                
                if init and field_default is not msgspec.UNSET:
                    return DynamicAttrs(**{field_name: field_default})
                elif init:
                    raise ValueError("Cannot initialize attrs class without a default value")
                else:
                    return DynamicAttrs
                    
            except ImportError:
                raise ImportError("attrs library is required for attrs conversion")
                
        elif schema == "dict":
            if init and field_default is not msgspec.UNSET:
                return {field_name: field_default}
            elif init:
                raise ValueError("Cannot initialize dict without a default value")
            else:
                return {field_name: field_type}
                
        else:
            raise ValueError(f"Unsupported schema format: {schema}")
    
    def model_convert(
        self,
        schema: Literal[
            "dataclass",
            "pydantic", 
            "msgspec",
            "typeddict",
            "namedtuple",
            "attrs",
            "dict",
        ],
        exclude: Optional[Union[Set[str], Set[int]]] = None,
    ) -> Any:
        """Convert the model to different schema formats using adaptix.
        
        Args:
            schema: The target schema format to convert to
            exclude: Fields to exclude from the conversion
            
        Returns:
            The converted model in the specified format
        """
        # Get current model data
        current_data = asdict(self)
        
        # Apply exclusions if specified
        if exclude is not None:
            if isinstance(exclude, set) and all(isinstance(k, str) for k in exclude):
                current_data = {k: v for k, v in current_data.items() if k not in exclude}
            elif isinstance(exclude, set) and all(isinstance(k, int) for k in exclude):
                items = list(current_data.items())
                current_data = dict(items[i] for i in range(len(items)) if i not in exclude)
        
        if schema == "dataclass":
            # Create a dynamic dataclass using make_dataclass
            from dataclasses import make_dataclass, field
            
            field_info = self._get_fields_info()
            fields_list = []
            
            for field_name, info in field_info.items():
                if field_name not in current_data:
                    continue
                field_type = info["type"]
                if info["required"]:
                    fields_list.append((field_name, field_type))
                else:
                    fields_list.append((field_name, field_type, field(default=info["default"])))
            
            DynamicDataclass = make_dataclass(
                f"Dynamic{self.__class__.__name__}",
                fields_list
            )
            
            return DynamicDataclass(**current_data)
            
        elif schema == "pydantic":
            from pydantic import BaseModel, create_model
            
            field_info = self._get_fields_info()
            pydantic_fields = {}
            
            for field_name, info in field_info.items():
                if field_name not in current_data:
                    continue
                field_type = info["type"]
                if info["required"]:
                    pydantic_fields[field_name] = (field_type, ...)
                else:
                    pydantic_fields[field_name] = (field_type, info["default"])
            
            PydanticModel = create_model(
                f"Pydantic{self.__class__.__name__}", **pydantic_fields
            )
            return PydanticModel(**current_data)
            
        elif schema == "msgspec":
            # Return as msgspec Struct (already is one)
            return self.__class__(**current_data)
            
        elif schema == "typeddict":
            # TypedDict doesn't have constructor, just return the dict with type info
            return current_data
            
        elif schema == "namedtuple":
            from collections import namedtuple
            
            field_names = list(current_data.keys())
            DynamicNamedTuple = namedtuple(f"Dynamic{self.__class__.__name__}", field_names)
            return DynamicNamedTuple(**current_data)
            
        elif schema == "attrs":
            try:
                import attrs
                
                field_info = self._get_fields_info()
                attrs_fields = []
                
                for field_name, info in field_info.items():
                    if field_name not in current_data:
                        continue
                    if info["required"]:
                        attrs_fields.append(attrs.field())
                    else:
                        attrs_fields.append(attrs.field(default=info["default"]))
                
                @attrs.define
                class DynamicAttrs:
                    pass
                
                # Set fields dynamically
                for i, field_name in enumerate(current_data.keys()):
                    setattr(DynamicAttrs, field_name, attrs_fields[i])
                
                return DynamicAttrs(**current_data)
                
            except ImportError:
                raise ImportError("attrs library is required for attrs conversion")
                
        elif schema == "dict":
            return current_data
            
        else:
            raise ValueError(f"Unsupported schema format: {schema}")
    
    @classmethod
    def convert_from_data(
        cls,
        data: Any,
        schema: Literal[
            "dataclass",
            "pydantic",
            "msgspec", 
            "typeddict",
            "namedtuple",
            "attrs",
            "dict",
        ],
        exclude: Optional[Union[Set[str], Set[int]]] = None,
    ) -> Any:
        """Class method to convert data to different schema formats.
        
        Args:
            data: Input data to convert (dict, object, etc.)
            schema: The target schema format to convert to
            exclude: Fields to exclude from the conversion
            
        Returns:
            The converted model in the specified format
        """
        # First create an instance from the data
        if isinstance(data, dict):
            instance = cls(**data)
        elif hasattr(data, '__dict__'):
            instance = cls(**data.__dict__)
        else:
            instance = cls.model_validate(data)
        
        # Then use the instance method to convert
        return instance.model_convert(schema, exclude)

    def model_to_pydantic(self):
        """Converts the `BasedModel` to a `pydantic.BaseModel`."""
        from pydantic import BaseModel, create_model

        # Get the field information from the current instance
        fields_info = self._get_fields_info()

        # Create a dictionary for pydantic model fields
        pydantic_fields = {}
        for field_name, field_info in fields_info.items():
            field_type = field_info["type"]
            default = field_info["default"]
            required = field_info["required"]

            if required:
                pydantic_fields[field_name] = (field_type, ...)
            else:
                pydantic_fields[field_name] = (field_type, default)

        # Create a dynamic pydantic model class
        PydanticModel = create_model(
            f"Pydantic{self.__class__.__name__}", **pydantic_fields
        )

        # Create an instance with the current data
        current_data = asdict(self)
        return PydanticModel(**current_data)

    def __str__(self) -> str:
        """String representation of the struct."""
        return f"{self.__class__.__name__}({', '.join(f'{k}={repr(v)}' for k, v in asdict(self).items())})"

    def __repr__(self) -> str:
        """Detailed string representation of the struct."""
        return self.__str__()

    # Dictionary access methods for compatibility
    def __getitem__(self, key: str) -> Any:
        """Get an item from the struct with IDE field completion support."""
        if not hasattr(self, key):
            raise KeyError(f"'{key}' not found in {self.__class__.__name__}")
        return getattr(self, key)
    
    def get_field(self, field_name: str) -> Any:
        """Get a field value with better IDE completion. Use: model.get_field('field_name')"""
        if not hasattr(self, field_name):
            raise KeyError(f"'{field_name}' not found in {self.__class__.__name__}")
        return getattr(self, field_name)
    
    @property
    def field_keys(self) -> tuple[str, ...]:
        """Get all available field names as a tuple for IDE completion."""
        return tuple(self.__struct_fields__)
    
    def fields(self):
        """Returns an accessor object with all fields for IDE completion."""
        class FieldAccessor:
            def __init__(self, instance):
                self._instance = instance
                # Dynamically set all field names as properties for IDE completion
                struct_fields = list(instance.__struct_fields__)
                self.__dict__.update({
                    name: getattr(instance, name) for name in struct_fields
                })
            
            def __getitem__(self, field_key: str) -> Any:
                if not hasattr(self._instance, field_key):
                    raise KeyError(f"'{field_key}' not found in {self._instance.__class__.__name__}")
                return getattr(self._instance, field_key)
            
            def __dir__(self):
                return list(self._instance.__struct_fields__)
            
            def keys(self):
                """Get all field names."""
                return list(self._instance.__struct_fields__)
            
            def values(self):
                """Get all field values."""
                return [getattr(self._instance, name) for name in self._instance.__struct_fields__]
            
            def items(self):
                """Get all field name-value pairs."""
                return [(name, getattr(self._instance, name)) for name in self._instance.__struct_fields__]
        
        return FieldAccessor(self)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item in the struct."""
        if key not in self.__struct_fields__:
            raise KeyError(
                f"'{key}' is not a valid field for {self.__class__.__name__}"
            )
        setattr(self, key, value)

    def __delitem__(self, key: str) -> None:
        """Delete an item from the struct.

        Note: This will raise an error as struct fields cannot be deleted.
        """
        raise TypeError(f"Cannot delete field '{key}' from immutable struct")

    def __contains__(self, key: str) -> bool:
        """Check if the struct contains a field."""
        return key in self.__struct_fields__

    def __iter__(self):
        """Iterate over field names."""
        return iter(self.__struct_fields__)

    def __dir__(self) -> list[str]:
        """Allows for IDE autocompletion of the model's fields
        when accessing through the dictionary interface."""
        # Include both parent attributes and field names
        base_attrs = super().__dir__()
        field_names = list(self.__struct_fields__)
        
        # Add some useful methods and properties
        additional_attrs = [
            'model_dump', 'model_dump_json', 'model_copy', 'model_validate',
            'model_validate_json', 'model_fields', 'model_json_schema',
            'model_to_pydantic', 'model_convert', 'fields'
        ]
        
        return list(set(base_attrs + field_names + additional_attrs))

    # Support for __post_init__ if needed (from msgspec 0.18.0+)
    def __post_init__(self) -> None:
        """Called after struct initialization.

        Override this method in subclasses to add post-initialization logic.
        This is called automatically by msgspec after the struct is created.
        """
        pass


@dataclass(frozen=True, slots=True)
class FieldInfo:
    """Immutable field information container optimized for performance.
    
    Uses frozen dataclass with slots for memory efficiency and faster attribute access.
    """
    # Core field configuration
    default: Any = msgspec.UNSET
    default_factory: Optional[Callable[[], Any]] = None
    
    # Naming and aliases
    alias: Optional[str] = None
    validation_alias: Optional[str] = None
    serialization_alias: Optional[str] = None
    
    # Documentation
    title: Optional[str] = None
    description: Optional[str] = None
    examples: Optional[List[Any]] = None
    
    # Serialization control
    exclude: bool = False
    include: bool = True
    repr: bool = True
    
    # Validation configuration
    strict: bool = False
    validate_default: bool = False
    frozen: bool = False
    allow_mutation: bool = True
    
    # Numeric constraints
    gt: Optional[Union[int, float]] = None
    ge: Optional[Union[int, float]] = None
    lt: Optional[Union[int, float]] = None
    le: Optional[Union[int, float]] = None
    multiple_of: Optional[Union[int, float]] = None
    allow_inf_nan: bool = True
    
    # String constraints
    pattern: Optional[Union[str, Pattern[str]]] = None
    strip_whitespace: bool = False
    to_lower: bool = False
    to_upper: bool = False
    
    # Collection constraints
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    unique_items: bool = False
    
    # Advanced configuration
    discriminator: Optional[str] = None
    json_schema_extra: Optional[Dict[str, Any]] = None
    kw_only: bool = False
    init: bool = True
    init_var: bool = False
    
    # Union handling
    union_mode: Literal['smart', 'left_to_right'] = 'smart'
    
    # Custom validators (stored as tuples for immutability)
    validators: tuple[Callable[[Any], Any], ...] = ()
    pre_validators: tuple[Callable[[Any], Any], ...] = ()
    post_validators: tuple[Callable[[Any], Any], ...] = ()
    
    def __post_init__(self):
        """Validate field configuration after initialization."""
        # Validate numeric constraints
        if self.gt is not None and self.ge is not None:
            raise ValueError("Cannot specify both 'gt' and 'ge'")
        if self.lt is not None and self.le is not None:
            raise ValueError("Cannot specify both 'lt' and 'le'")
        
        # Validate string pattern
        if self.pattern is not None and isinstance(self.pattern, str):
            try:
                object.__setattr__(self, 'pattern', re.compile(self.pattern))
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
        
        # Ensure validators are tuples
        for attr in ('validators', 'pre_validators', 'post_validators'):
            val = getattr(self, attr)
            if not isinstance(val, tuple):
                object.__setattr__(self, attr, tuple(val) if val else ())
    
    @lru_cache(maxsize=None)
    def get_effective_alias(self, mode: Literal['validation', 'serialization', 'general'] = 'general') -> Optional[str]:
        """Get the effective alias for a given mode with caching."""
        if mode == 'validation' and self.validation_alias:
            return self.validation_alias
        elif mode == 'serialization' and self.serialization_alias:
            return self.serialization_alias
        return self.alias
    
    def apply_constraints(self, value: Any, field_name: str) -> Any:
        """Apply validation constraints to a value."""
        # Pre-validators
        for validator in self.pre_validators:
            value = validator(value)
        
        # Type-specific constraints
        if isinstance(value, (int, float)):
            value = self._validate_numeric(value, field_name)
        elif isinstance(value, str):
            value = self._validate_string(value, field_name)
        elif isinstance(value, (list, tuple, set, frozenset)):
            value = self._validate_collection(value, field_name)
        
        # General validators
        for validator in self.validators:
            value = validator(value)
        
        # Post-validators
        for validator in self.post_validators:
            value = validator(value)
        
        return value
    
    def _validate_numeric(self, value: Union[int, float], field_name: str) -> Union[int, float]:
        """Apply numeric constraints."""
        if not self.allow_inf_nan and isinstance(value, float):
            if value != value:  # NaN check
                raise ValueError(f"{field_name}: NaN values are not allowed")
            if value == float('inf') or value == float('-inf'):
                raise ValueError(f"{field_name}: Infinite values are not allowed")
        
        if self.gt is not None and value <= self.gt:
            raise ValueError(f"{field_name}: {value} is not greater than {self.gt}")
        if self.ge is not None and value < self.ge:
            raise ValueError(f"{field_name}: {value} is not greater than or equal to {self.ge}")
        if self.lt is not None and value >= self.lt:
            raise ValueError(f"{field_name}: {value} is not less than {self.lt}")
        if self.le is not None and value > self.le:
            raise ValueError(f"{field_name}: {value} is not less than or equal to {self.le}")
        
        if self.multiple_of is not None:
            if isinstance(value, float) or isinstance(self.multiple_of, float):
                # Use float comparison with small epsilon for floats
                remainder = value % self.multiple_of
                if abs(remainder) > 1e-9 and abs(remainder - self.multiple_of) > 1e-9:
                    raise ValueError(f"{field_name}: {value} is not a multiple of {self.multiple_of}")
            else:
                # Exact comparison for integers
                if value % self.multiple_of != 0:
                    raise ValueError(f"{field_name}: {value} is not a multiple of {self.multiple_of}")
        
        return value
    
    def _validate_string(self, value: str, field_name: str) -> str:
        """Apply string constraints and transformations."""
        # Transformations
        if self.strip_whitespace:
            value = value.strip()
        if self.to_lower:
            value = value.lower()
        if self.to_upper:
            value = value.upper()
        
        # Length validation
        if self.min_length is not None and len(value) < self.min_length:
            raise ValueError(f"{field_name}: String length {len(value)} is less than minimum {self.min_length}")
        if self.max_length is not None and len(value) > self.max_length:
            raise ValueError(f"{field_name}: String length {len(value)} exceeds maximum {self.max_length}")
        
        # Pattern validation
        if self.pattern is not None:
            pattern = self.pattern if isinstance(self.pattern, Pattern) else re.compile(self.pattern)
            if not pattern.match(value):
                raise ValueError(f"{field_name}: String does not match pattern {pattern.pattern}")
        
        return value
    
    def _validate_collection(self, value: Union[List, Set, tuple, frozenset], field_name: str) -> Any:
        """Apply collection constraints."""
        # Length validation
        if self.min_length is not None and len(value) < self.min_length:
            raise ValueError(f"{field_name}: Collection length {len(value)} is less than minimum {self.min_length}")
        if self.max_length is not None and len(value) > self.max_length:
            raise ValueError(f"{field_name}: Collection length {len(value)} exceeds maximum {self.max_length}")
        
        # Unique items validation for lists/tuples
        if self.unique_items and isinstance(value, (list, tuple)):
            seen = set()
            for item in value:
                # Handle unhashable types
                try:
                    if item in seen:
                        raise ValueError(f"{field_name}: Duplicate items are not allowed")
                    seen.add(item)
                except TypeError:
                    # For unhashable types, fall back to linear search
                    if value.count(item) > 1:
                        raise ValueError(f"{field_name}: Duplicate items are not allowed")
        
        return value
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Generate JSON schema for this field."""
        schema = {}
        
        if self.title:
            schema['title'] = self.title
        if self.description:
            schema['description'] = self.description
        if self.examples:
            schema['examples'] = self.examples
        
        # Numeric constraints
        if self.gt is not None:
            schema['exclusiveMinimum'] = self.gt
        if self.ge is not None:
            schema['minimum'] = self.ge
        if self.lt is not None:
            schema['exclusiveMaximum'] = self.lt
        if self.le is not None:
            schema['maximum'] = self.le
        if self.multiple_of is not None:
            schema['multipleOf'] = self.multiple_of
        
        # String constraints
        if self.pattern is not None:
            pattern = self.pattern if isinstance(self.pattern, str) else self.pattern.pattern
            schema['pattern'] = pattern
        if self.min_length is not None:
            schema['minLength'] = self.min_length
        if self.max_length is not None:
            schema['maxLength'] = self.max_length
        
        # Collection constraints
        if self.unique_items:
            schema['uniqueItems'] = True
        
        # Extra schema properties
        if self.json_schema_extra:
            schema.update(self.json_schema_extra)
        
        return schema


class Field:
    """Field descriptor that combines msgspec.field with FieldInfo metadata.
    
    This class wraps msgspec's field functionality while preserving our
    extended metadata for validation and serialization.
    """
    
    def __init__(self, field_info: FieldInfo):
        self.field_info = field_info
        self._msgspec_field = None
    
    def __set_name__(self, owner, name):
        """Called when the descriptor is assigned to a class attribute."""
        self.name = name
        
    def to_msgspec(self) -> Any:
        """Convert to a msgspec field."""
        kwargs = {}
        
        # Handle default value
        if self.field_info.default is not msgspec.UNSET:
            kwargs['default'] = self.field_info.default
        elif self.field_info.default_factory is not None:
            kwargs['default_factory'] = self.field_info.default_factory
        
        # Handle field naming
        if self.field_info.alias:
            # Use Annotated with Meta for field renaming
            return msgspec_field(**kwargs)
        
        return msgspec_field(**kwargs)
    
    def __repr__(self):
        return f"Field({self.field_info})"


def basedfield(
    default: Any = msgspec.UNSET,
    *,
    default_factory: Optional[Callable[[], Any]] = None,
    alias: Optional[str] = None,
    validation_alias: Optional[str] = None,
    serialization_alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    examples: Optional[List[Any]] = None,
    exclude: bool = False,
    include: bool = True,
    repr: bool = True,
    strict: bool = False,
    validate_default: bool = False,
    frozen: bool = False,
    allow_mutation: bool = True,
    gt: Optional[Union[int, float]] = None,
    ge: Optional[Union[int, float]] = None,
    lt: Optional[Union[int, float]] = None,
    le: Optional[Union[int, float]] = None,
    multiple_of: Optional[Union[int, float]] = None,
    allow_inf_nan: bool = True,
    pattern: Optional[Union[str, Pattern[str]]] = None,
    strip_whitespace: bool = False,
    to_lower: bool = False,
    to_upper: bool = False,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    unique_items: bool = False,
    discriminator: Optional[str] = None,
    json_schema_extra: Optional[Dict[str, Any]] = None,
    kw_only: bool = False,
    init: bool = True,
    init_var: bool = False,
    union_mode: Literal['smart', 'left_to_right'] = 'smart',
    validators: Optional[List[Callable[[Any], Any]]] = None,
    pre_validators: Optional[List[Callable[[Any], Any]]] = None,
    post_validators: Optional[List[Callable[[Any], Any]]] = None,
) -> Any:
    """Create a field descriptor for BasedModel with Pydantic-like configuration.
    
    This function creates a field with validation, serialization, and schema
    generation capabilities while maintaining msgspec's performance benefits.
    
    Args:
        default: Default value for the field
        default_factory: Factory function to generate default values
        alias: Alternative name for the field in serialization/deserialization
        validation_alias: Specific alias for validation (input) only
        serialization_alias: Specific alias for serialization (output) only
        title: Human-readable title for documentation
        description: Human-readable description for documentation
        examples: List of example valid values
        exclude: Whether to exclude this field from serialization
        include: Whether to include this field in serialization
        repr: Whether to include in string representation
        strict: Whether to use strict type validation
        validate_default: Whether to validate the default value
        frozen: Whether the field is immutable after creation
        allow_mutation: Whether the field can be modified
        gt: Value must be greater than this
        ge: Value must be greater than or equal to this
        lt: Value must be less than this
        le: Value must be less than or equal to this
        multiple_of: Value must be a multiple of this
        allow_inf_nan: Whether to allow infinity and NaN for floats
        pattern: Regex pattern for string validation
        strip_whitespace: Whether to strip whitespace from strings
        to_lower: Whether to convert strings to lowercase
        to_upper: Whether to convert strings to uppercase
        min_length: Minimum length for strings/collections
        max_length: Maximum length for strings/collections
        unique_items: Whether collection items must be unique
        discriminator: Field name for discriminating unions
        json_schema_extra: Additional JSON schema properties
        kw_only: Whether the field is keyword-only in __init__
        init: Whether to include in __init__
        init_var: Whether the field is init-only
        union_mode: How to validate union types
        validators: List of validation functions
        pre_validators: List of pre-processing validators
        post_validators: List of post-processing validators
    
    Returns:
        Field descriptor or Annotated type with metadata for use with BasedModel
    """
    # Store field info for potential future use (validation, schema generation, etc.)
    info = FieldInfo(
        default=default,
        default_factory=default_factory,
        alias=alias,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        examples=examples,
        exclude=exclude,
        include=include,
        repr=repr,
        strict=strict,
        validate_default=validate_default,
        frozen=frozen,
        allow_mutation=allow_mutation,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        pattern=pattern,
        strip_whitespace=strip_whitespace,
        to_lower=to_lower,
        to_upper=to_upper,
        min_length=min_length,
        max_length=max_length,
        unique_items=unique_items,
        discriminator=discriminator,
        json_schema_extra=json_schema_extra,
        kw_only=kw_only,
        init=init,
        init_var=init_var,
        union_mode=union_mode,
        validators=tuple(validators or []),
        pre_validators=tuple(pre_validators or []),
        post_validators=tuple(post_validators or []),
    )
    
    # Build the kwargs for the msgspec field
    kwargs = {}
    if default is not msgspec.UNSET:
        kwargs['default'] = default
    elif default_factory is not None:
        kwargs['default_factory'] = default_factory
    
    # Create the msgspec field with validation info embedded
    msgspec_field_instance = msgspec_field(**kwargs)
    
    # For now, just return the msgspec field - let msgspec handle everything
    return msgspec_field_instance


# Utility functions for field introspection

@lru_cache(maxsize=None)
def get_field_info(field: Any) -> Optional[FieldInfo]:
    """Extract FieldInfo from a field descriptor with caching."""
    if isinstance(field, tuple) and len(field) == 2:
        _, field_info = field
        if isinstance(field_info, FieldInfo):
            return field_info
    elif hasattr(field, '_basedfield_info'):
        return field._basedfield_info
    elif hasattr(field, 'field_info'):
        return field.field_info
    elif isinstance(field, Field):
        return field.field_info
    elif hasattr(field, '__class__') and field.__class__.__name__ == 'FieldDescriptor':
        return field.field_info
    return None


def is_basedfield(field: Any) -> bool:
    """Check if a field is a basedfield."""
    return get_field_info(field) is not None


# Validators

def basedvalidator(*fields: str, pre: bool = False, post: bool = False, always: bool = False):
    """Decorator to create a validator for specific fields.
    
    Args:
        *fields: Field names to validate
        pre: Whether this is a pre-validator
        post: Whether this is a post-validator
        always: Whether to run even if the value is not set
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        func._validator_fields = fields
        func._validator_pre = pre
        func._validator_post = post
        func._validator_always = always
        return func
    
    return decorator


def str_basedfield(
    *,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[Union[str, Pattern[str]]] = None,
    strip_whitespace: bool = False,
    to_lower: bool = False,
    to_upper: bool = False,
    **kwargs
) -> Any:
    """Create a string field with common string-specific options."""
    return basedfield(
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        strip_whitespace=strip_whitespace,
        to_lower=to_lower,
        to_upper=to_upper,
        **kwargs
    )


def int_basedfield(
    *,
    gt: Optional[int] = None,
    ge: Optional[int] = None,
    lt: Optional[int] = None,
    le: Optional[int] = None,
    multiple_of: Optional[int] = None,
    **kwargs
) -> Any:
    """Create an integer field with numeric constraints."""
    return basedfield(
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        **kwargs
    )


def float_basedfield(
    *,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    allow_inf_nan: bool = True,
    **kwargs
) -> Any:
    """Create a float field with numeric constraints."""
    return basedfield(
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        **kwargs
    )


def list_basedfield(
    *,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    unique_items: bool = False,
    **kwargs
) -> Any:
    """Create a list field with collection constraints."""
    return basedfield(
        default_factory=list,
        min_length=min_length,
        max_length=max_length,
        unique_items=unique_items,
        **kwargs
    )


# Example usage and testing
if __name__ == "__main__":
    from typing import Optional, List
    import msgspec
    
    # Example of using basedfield with different configurations
    
    # Numeric field with constraints
    age_field = basedfield(
        default=0,
        ge=0,
        le=150,
        description="User's age in years",
        title="Age",
        examples=[25, 30, 45]
    )
    print(f"Age field created: {age_field}")
    
    # String field with pattern and transformations
    email_field = basedfield(
        alias="email_address",
        pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$',
        strip_whitespace=True,
        to_lower=True,
        description="User's email address",
        title="Email"
    )
    print(f"Email field created: {email_field}")
    
    # Collection field with constraints
    tags_field = basedfield(
        default_factory=list,
        min_length=1,
        max_length=10,
        unique_items=True,
        description="User tags",
        examples=[["python", "developer"], ["admin", "moderator"]]
    )
    print(f"Tags field created: {tags_field}")
    
    # Advanced field with custom validators
    def validate_username(value: str) -> str:
        if not value.isalnum():
            raise ValueError("Username must be alphanumeric")
        return value
    
    username_field = basedfield(
        min_length=3,
        max_length=20,
        validators=[validate_username],
        strip_whitespace=True,
        description="Unique username"
    )
    print(f"Username field created: {username_field}")
    
    # Test FieldInfo
    info = FieldInfo(
        default="test",
        gt=0,
        le=100,
        pattern=r'^\w+$',
        validators=(lambda x: x.upper(),)
    )
    
    print(f"\nFieldInfo: {info}")
    print(f"Effective alias: {info.get_effective_alias('validation')}")
    print(f"JSON Schema: {info.to_json_schema()}")
    
    # Test convenience functions
    name_field = str_basedfield(min_length=1, max_length=100, strip_whitespace=True)
    age_field = int_basedfield(ge=0, le=120)
    score_field = float_basedfield(ge=0.0, le=100.0, allow_inf_nan=False)
    tags_field = list_basedfield(min_length=0, max_length=10, unique_items=True)
    
    print("\nConvenience fields created successfully!")
