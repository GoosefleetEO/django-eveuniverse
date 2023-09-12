"""Base models for Eve Universe."""

import enum
from collections import namedtuple
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from django.apps import apps
from django.db import models

from eveuniverse.managers import EveUniverseEntityModelManager

NAMES_MAX_LENGTH = 100

EsiMapping = namedtuple(
    "EsiMapping",
    [
        "esi_name",
        "is_optional",
        "is_pk",
        "is_fk",
        "related_model",
        "is_parent_fk",
        "is_charfield",
        "create_related",
    ],
)
"""
:meta private:
"""


class _SectionBase(str, enum.Enum):
    """Base class for all Sections"""

    @classmethod
    def values(cls) -> list:
        """Return values for the sections."""
        return list(item.value for item in cls)

    def __str__(self) -> str:
        return self.value


class EveUniverseBaseModel(models.Model):
    """Base class for all Eve Universe Models.

    :meta private:
    """

    class Meta:
        abstract = True

    def __repr__(self) -> str:
        """General purpose __repr__ that works for all model classes"""
        fields = sorted(
            [
                f
                for f in self._meta.get_fields()
                if isinstance(f, models.Field) and f.name != "last_updated"
            ],
            key=lambda x: x.name,
        )
        fields_2 = []
        for field in fields:
            if field.many_to_one or field.one_to_one:
                name = f"{field.name}_id"
                value = getattr(self, name)
            elif field.many_to_many:
                name = field.name
                value = ", ".join(
                    sorted([str(x) for x in getattr(self, field.name).all()])
                )
            else:
                name = field.name
                value = getattr(self, field.name)

            if isinstance(value, str):
                if isinstance(field, models.TextField) and len(value) > 32:
                    value = f"{value[:32]}..."
                text = f"{name}='{value}'"
            else:
                text = f"{name}={value}"

            fields_2.append(text)

        return f"{self.__class__.__name__}({', '.join(fields_2)})"

    @classmethod
    def all_models(cls) -> List[Dict[models.Model, int]]:
        """Return a list of all Eve Universe model classes sorted by load order."""
        mappings = []
        for model_class in apps.get_models():
            if model_class._meta.app_label != "eveuniverse":
                continue

            if issubclass(
                model_class, (EveUniverseEntityModel, EveUniverseInlineModel)
            ) and model_class not in (
                cls,
                EveUniverseEntityModel,
                EveUniverseInlineModel,
            ):
                mappings.append(
                    {
                        "model": model_class,
                        "load_order": model_class._eve_universe_meta_attr_strict(
                            "load_order"
                        ),
                    }
                )

        return [y["model"] for y in sorted(mappings, key=lambda x: x["load_order"])]

    @classmethod
    def get_model_class(cls, model_name: str):
        """returns the model class for the given name"""
        model_class = apps.get_model("eveuniverse", model_name)
        if not issubclass(model_class, (EveUniverseBaseModel, EveUniverseInlineModel)):
            raise TypeError("Invalid model class")
        return model_class

    @classmethod
    def _esi_pk(cls) -> str:
        """returns the name of the pk column on ESI that must exist"""
        return cls._eve_universe_meta_attr_strict("esi_pk")

    @classmethod
    def _esi_mapping(cls, enabled_sections: Optional[Set[str]] = None) -> dict:
        field_mappings = cls._eve_universe_meta_attr("field_mappings")
        functional_pk = cls._eve_universe_meta_attr("functional_pk")
        parent_fk = cls._eve_universe_meta_attr("parent_fk")
        dont_create_related = cls._eve_universe_meta_attr("dont_create_related")
        disabled_fields = cls._disabled_fields(enabled_sections)
        mapping = {}
        for field in [
            field
            for field in cls._meta.get_fields()
            if not field.auto_created
            and field.name not in {"last_updated", "enabled_sections"}
            and field.name not in disabled_fields
            and not field.many_to_many
        ]:
            if field_mappings and field.name in field_mappings:
                esi_name = field_mappings[field.name]
            else:
                esi_name = field.name

            if field.primary_key is True:
                is_pk = True
                esi_name = cls._esi_pk()
            elif functional_pk and field.name in functional_pk:
                is_pk = True
            else:
                is_pk = False

            is_parent_fk = bool(parent_fk and is_pk and field.name in parent_fk)

            if isinstance(field, models.ForeignKey):
                is_fk = True
                related_model = field.related_model
            else:
                is_fk = False
                related_model = None

            if dont_create_related and field.name in dont_create_related:
                create_related = False
            else:
                create_related = True

            mapping[field.name] = EsiMapping(
                esi_name=esi_name,
                is_optional=field.has_default(),
                is_pk=is_pk,
                is_fk=is_fk,
                related_model=related_model,
                is_parent_fk=is_parent_fk,
                is_charfield=isinstance(field, (models.CharField, models.TextField)),
                create_related=create_related,
            )

        return mapping

    @classmethod
    def _disabled_fields(cls, _enabled_sections: Optional[Set[str]] = None) -> set:
        """Return name of fields that must not be loaded from ESI."""
        return set()

    @classmethod
    def _eve_universe_meta_attr(cls, attr_name: str) -> Optional[Any]:
        """Return value of an attribute from EveUniverseMeta or None"""
        return cls._eve_universe_meta_attr_flexible(attr_name, is_mandatory=False)

    @classmethod
    def _eve_universe_meta_attr_strict(cls, attr_name: str) -> Any:
        """Return value of an attribute from EveUniverseMeta or raise exception."""
        return cls._eve_universe_meta_attr_flexible(attr_name, is_mandatory=True)

    @classmethod
    def _eve_universe_meta_attr_flexible(
        cls, attr_name: str, is_mandatory: bool = False
    ) -> Optional[Any]:
        try:
            value = getattr(cls._EveUniverseMeta, attr_name)  # type: ignore
        except AttributeError:
            value = None
            if is_mandatory:
                raise ValueError(
                    f"Mandatory attribute EveUniverseMeta.{attr_name} not defined "
                    f"for class {cls.__name__}"
                ) from None

        return value

    # TODO: Add unit tests
    @classmethod
    def defaults_from_esi_obj(
        cls, eve_data_obj: dict, enabled_sections: Optional[Set[str]] = None
    ) -> dict:
        """Return defaults from an esi data object
        for update/creating objects of this model.
        """
        defaults = {}
        for field_name, mapping in cls._esi_mapping(enabled_sections).items():
            if mapping.is_pk:
                continue

            if not isinstance(mapping.esi_name, tuple):
                esi_value = cls._esi_value_from_tuple(eve_data_obj, mapping)
            else:
                esi_value = cls._esi_value_from_non_tuple(eve_data_obj, mapping)

            if esi_value is not None:
                if mapping.is_fk:
                    value = cls._gather_value_from_fk(mapping, esi_value)

                else:
                    if mapping.is_charfield and esi_value is None:
                        value = ""
                    else:
                        value = esi_value

                defaults[field_name] = value

        return defaults

    @staticmethod
    def _esi_value_from_tuple(eve_data_obj, mapping) -> Optional[Any]:
        if mapping.esi_name in eve_data_obj:
            return eve_data_obj[mapping.esi_name]
        return None

    @staticmethod
    def _esi_value_from_non_tuple(eve_data_obj, mapping) -> Optional[Any]:
        if (
            mapping.esi_name[0] in eve_data_obj
            and mapping.esi_name[1] in eve_data_obj[mapping.esi_name[0]]
        ):
            return eve_data_obj[mapping.esi_name[0]][mapping.esi_name[1]]

        return None

    @staticmethod
    def _gather_value_from_fk(mapping, esi_value):
        parent_class = mapping.related_model
        try:
            value = parent_class.objects.get(id=esi_value)
        except parent_class.DoesNotExist:
            value = None
            if mapping.create_related:
                try:
                    value = parent_class.objects.update_or_create_esi(
                        id=esi_value, include_children=False, wait_for_children=True
                    )[0]
                except AttributeError:
                    pass
        return value


class EveUniverseEntityModel(EveUniverseBaseModel):
    """Base class for Eve Universe Entity models.

    Entity models are normal Eve entities that have a dedicated ESI endpoint.

    :meta private:
    """

    class Section(_SectionBase):
        """A section."""

    # sections
    LOAD_DOGMAS = "dogmas"
    # TODO: Implement other sections

    # icons
    DEFAULT_ICON_SIZE = 64

    id = models.PositiveIntegerField(primary_key=True, help_text="Eve Online ID")
    name = models.CharField(
        max_length=NAMES_MAX_LENGTH,
        default="",
        db_index=True,
        help_text="Eve Online name",
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="When this object was last updated from ESI",
        db_index=True,
    )

    objects = EveUniverseEntityModelManager()

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name

    @classmethod
    def update_or_create_children(
        cls,
        *,
        parent_eve_data_obj: dict,
        include_children: bool,
        wait_for_children: bool,
        enabled_sections: Iterable[str],
        task_priority: Optional[int] = None,
    ) -> None:
        """updates or creates child objects as defined for this parent model (if any)"""
        from eveuniverse.tasks import (
            update_or_create_eve_object as task_update_or_create_eve_object,
        )

        if not parent_eve_data_obj:
            raise ValueError(
                f"{cls.__name__}: Tried to create children from empty parent object"
            )

        for key, child_class in cls._children(enabled_sections).items():
            if key in parent_eve_data_obj and parent_eve_data_obj[key]:
                for obj in parent_eve_data_obj[key]:
                    # TODO: Refactor this hack
                    id = obj["planet_id"] if key == "planets" else obj
                    if wait_for_children:
                        child_model_class = cls.get_model_class(child_class)
                        child_model_class.objects.update_or_create_esi(
                            id=id,
                            include_children=include_children,
                            wait_for_children=wait_for_children,
                            enabled_sections=enabled_sections,
                            task_priority=task_priority,
                        )

                    else:
                        params: Dict[str, Any] = {
                            "kwargs": {
                                "model_name": child_class,
                                "id": id,
                                "include_children": include_children,
                                "wait_for_children": wait_for_children,
                                "enabled_sections": list(enabled_sections),
                                "task_priority": task_priority,
                            },
                        }
                        if task_priority:
                            params["priority"] = task_priority
                        task_update_or_create_eve_object.apply_async(**params)  # type: ignore

    @classmethod
    def update_or_create_inline_objects(
        cls,
        *,
        parent_eve_data_obj: dict,
        parent_obj,
        wait_for_children: bool,
        enabled_sections: Iterable[str],
        task_priority: Optional[int] = None,
    ) -> None:
        """updates_or_creates eve objects that are returned "inline" from ESI
        for the parent eve objects as defined for this parent model (if any)
        """
        from eveuniverse.tasks import (
            update_or_create_inline_object as task_update_or_create_inline_object,
        )

        inline_objects = cls._inline_objects(enabled_sections)
        if not inline_objects:
            return

        if not parent_eve_data_obj or not parent_obj:
            raise ValueError(
                f"{cls.__name__}: Tried to create inline object "
                "from empty parent object"
            )

        for inline_field, inline_model_name in inline_objects.items():
            if (
                inline_field not in parent_eve_data_obj
                or not parent_eve_data_obj[inline_field]
            ):
                continue

            parent_fk, parent2_model_name, other_pk_info = cls._identify_parent(
                inline_model_name
            )

            for eve_data_obj in parent_eve_data_obj[inline_field]:
                if wait_for_children:
                    cls.update_or_create_inline_object(
                        parent_obj_id=parent_obj.id,
                        parent_fk=parent_fk,
                        eve_data_obj=eve_data_obj,
                        other_pk_info=other_pk_info,
                        parent2_model_name=parent2_model_name,
                        inline_model_name=inline_model_name,
                        enabled_sections=enabled_sections,
                    )
                else:
                    params: Dict[str, Any] = {
                        "kwargs": {
                            "parent_obj_id": parent_obj.id,
                            "parent_fk": parent_fk,
                            "eve_data_obj": eve_data_obj,
                            "other_pk_info": other_pk_info,
                            "parent2_model_name": parent2_model_name,
                            "inline_model_name": inline_model_name,
                            "parent_model_name": type(parent_obj).__name__,
                            "enabled_sections": list(enabled_sections),
                        }
                    }
                    if task_priority:
                        params["priority"] = task_priority
                    task_update_or_create_inline_object.apply_async(**params)  # type: ignore

    @classmethod
    def _identify_parent(cls, inline_model_name: str) -> tuple:
        inline_model_class = cls.get_model_class(inline_model_name)
        esi_mapping = inline_model_class._esi_mapping()
        parent_fk = None
        other_pk = None
        parent_class_2 = None
        for field_name, mapping in esi_mapping.items():
            if mapping.is_pk:
                if mapping.is_parent_fk:
                    parent_fk = field_name
                else:
                    other_pk = (field_name, mapping)
                    parent_class_2 = mapping.related_model

        if not parent_fk or not other_pk:
            raise ValueError(
                f"ESI Mapping for {inline_model_name} not valid: {parent_fk}, {other_pk}"
            )

        parent2_model_name = parent_class_2.__name__ if parent_class_2 else None
        other_pk_info = {
            "name": other_pk[0],
            "esi_name": other_pk[1].esi_name,
            "is_fk": other_pk[1].is_fk,
        }
        return parent_fk, parent2_model_name, other_pk_info

    @classmethod
    def update_or_create_inline_object(
        cls,
        parent_obj_id: int,
        parent_fk: str,
        eve_data_obj: dict,
        other_pk_info: Dict[str, Any],
        parent2_model_name: Optional[str],
        inline_model_name: str,
        enabled_sections: Iterable[str],
    ):
        """Updates or creates a single inline object.
        Will automatically create additional parent objects as needed
        """
        inline_model_class = cls.get_model_class(inline_model_name)

        args = {f"{parent_fk}_id": parent_obj_id}
        esi_value = eve_data_obj.get(other_pk_info["esi_name"])
        if other_pk_info["is_fk"]:
            parent_class_2 = cls.get_model_class(parent2_model_name)
            try:
                value = parent_class_2.objects.get(id=esi_value)
            except parent_class_2.DoesNotExist:
                try:
                    value, _ = parent_class_2.objects.update_or_create_esi(
                        id=esi_value, enabled_sections=enabled_sections
                    )
                except AttributeError:
                    value = None
        else:
            value = esi_value

        key = other_pk_info["name"]
        args[key] = value  # type: ignore
        args["defaults"] = inline_model_class.defaults_from_esi_obj(
            eve_data_obj, enabled_sections=enabled_sections
        )
        inline_model_class.objects.update_or_create(**args)

    @classmethod
    def eve_entity_category(cls) -> str:
        """returns the EveEntity category of this model if one exists
        else and empty string
        """
        return ""

    @classmethod
    def _has_esi_path_list(cls) -> bool:
        return bool(cls._eve_universe_meta_attr("esi_path_list"))

    @classmethod
    def _esi_path_list(cls) -> Tuple[str, str]:
        return cls._esi_path("list")

    @classmethod
    def _esi_path_object(cls) -> Tuple[str, str]:
        return cls._esi_path("object")

    @classmethod
    def _esi_path(cls, variant: str) -> Tuple[str, str]:
        attr_name = f"esi_path_{str(variant)}"
        path = cls._eve_universe_meta_attr_strict(attr_name)
        if len(path.split(".")) != 2:
            raise ValueError(f"{attr_name} not valid")
        return path.split(".")

    @classmethod
    def _children(cls, _enabled_sections: Optional[Iterable[str]] = None) -> dict:
        """returns the mapping of children for this class"""
        mappings = cls._eve_universe_meta_attr("children")
        return mappings if mappings else {}

    @classmethod
    def _inline_objects(cls, _enabled_sections: Optional[Set[str]] = None) -> dict:
        """returns a dict of inline objects if any"""
        inline_objects = cls._eve_universe_meta_attr("inline_objects")
        return inline_objects if inline_objects else {}

    @classmethod
    def _is_list_only_endpoint(cls) -> bool:
        esi_path_list = cls._eve_universe_meta_attr("esi_path_list")
        esi_path_object = cls._eve_universe_meta_attr("esi_path_object")
        return (
            bool(esi_path_list)
            and bool(esi_path_object)
            and esi_path_list == esi_path_object
        )


class EveUniverseInlineModel(EveUniverseBaseModel):
    """Base class for Eve Universe Inline models.

    Inline models are objects which do not have a dedicated ESI endpoint and are
    provided through the endpoint of another entity

    This class is also used for static Eve data.

    :meta private:
    """

    class Meta:
        abstract = True
