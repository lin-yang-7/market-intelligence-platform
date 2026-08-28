from typing import Any

from pydantic import BaseModel


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def model_to_json(model: BaseModel) -> str:
    if hasattr(model, "model_dump_json"):
        return model.model_dump_json()
    return model.json()


def validate_model(model_class, value):
    if hasattr(model_class, "model_validate"):
        return model_class.model_validate(value)
    return model_class.parse_obj(value)


def model_copy_with_update(model: BaseModel, update: dict[str, Any]) -> BaseModel:
    if hasattr(model, "model_copy"):
        return model.model_copy(update=update)
    return model.copy(update=update)
