"""
Pathbuilder 2e
"""

from typing import Optional
from dataclasses import dataclass, field

import json
import re
import yaml

PARAGRAPH_BREAK: re.Pattern[str] = re.compile(r"(?:\n\s*?){2,}\s*")
WHITESPACE: re.Pattern[str]      = re.compile(r"\s+")


@dataclass(eq=True, frozen=True, kw_only=True)
class Background:  # pylint: disable=too-many-instance-attributes
    """
    Represents a Pathbuilder 2e background.

    Attributes:
        databaseID (int):  The background's database ID.
        id (str):          The background's ID.
        name (str):        The background's name.
        traits (str):      The background's traits.
        boost_ref_1 (str): The background's first boost reference.
        boost_ref_2 (str): The background's second boost reference.
        freeFeatID (str):  The background's free feat ID.
        skill (str):       The background's skill.
        lore (str):        The background's lore.
        description (str): The background's description.
        src (str):         The background's source.
    """
    databaseID:  int # pylint: disable=invalid-name
    id:          str
    name:        str
    traits:      str
    boost_ref_1: str
    boost_ref_2: str
    freeFeatID:  str # pylint: disable=invalid-name
    skill:       str
    lore:        str
    description: str
    src:         str


    def find_matching_source(self, sources: list["BackgroundSource"]) -> "BackgroundSource|None":
        """
        Returns the first matching background source background from the given
        list. If no match is found, it returns None. A source is considered a
        match if it has the same name or ID.

        Parameters:
            sources (list[BackgroundSource]): List of BackgroundSource objects to search.

        Returns:
            BackgroundSource|None: The first matching source or None if no match is found.
        """
        return next((source for source in sources if source.is_match(self)), None)


    def updated_from_source(self, source: "BackgroundSource"):
        """
        Returns a copy of this background updated from the given background
        source. If source is None, the background is returned unchanged.

        Parameters:
            source (BackgroundSource): The background source

        Returns:
            The updated background.
        """
        params = self.__dict__.copy()
        params["id"] = source.id or self.id
        params["lore"] = source.lore or self.lore
        params["name"] = source.name
        params["traits"] = ", ".join(source.traits)
        params["description"] = source.normalized_description
        params["src"] = source.src
        return Background(**params)


@dataclass(eq=True, frozen=True, kw_only=True)
class BackgroundSource:
    """
    Represents a source background.

    Attributes:
        id (Optional[str]):   The background's ID.
        name (str):           The background's name.
        traits (list[str]):   The background's traits.
        lore (Optional[str]): The background's lore.
        description (str):    The background's description.
        src (str):            The background's source.
    """
    id:          Optional[str] = field(default=None)
    name:        str
    traits:      list[str]     = field(default_factory=lambda: ["3rd Party"])
    lore:        Optional[str] = field(default=None)
    description: str
    src:         str           = field(default="Custom")


    @property
    def normalized_description(self) -> str:
        """
        Replaces sequences of two or more line breaks with HTML line breaks
        and reduces all other whitespace to a single space.

        Returns:
            str: The normalized description.
        """

        text = PARAGRAPH_BREAK.sub("<br>", self.description)
        return WHITESPACE.sub(" ", text).strip()


    def is_match(self, background: Background) -> bool:
        """
        Checks if the given background matches this source.

        Parameters:
            background (Background): The background to check.

        Returns:
            bool: True if the background matches this source, False otherwise.
        """
        return self.name == background.name or self.id == background.id


    @staticmethod
    def load(filepath: str) -> list["BackgroundSource"]:
        """
        Loads source backgrounds from the given YAML file.

        Parameters:
            filepath (str): Path to the YAML file to load.

        Returns:
            list[BackgroundSource]: List of loaded source backgrounds.
        """

        with open(filepath, "r", encoding="utf-8") as file:
            sources = [BackgroundSource(**attrs) for attrs in yaml.safe_load(file)]
        return sources


@dataclass(eq=True, frozen=True, kw_only=True)
class Pack:
    """
    Represents a pack of custom Pathbuilder 2e backgrounds.

    Attributes:
        customPackID (str):                       The pack's ID.
        customPackName (str):                     The pack's name.
        listCustomBackgrounds (list[Background]): List of custom Pathbuilder 2e backgrounds.
    """
    # pylint: disable=invalid-name
    customPackID:          str
    customPackName:        str
    listCustomBackgrounds: list[Background] = field(default_factory=list)
    # pylint: enable=invalid-name


    @staticmethod
    def load(filepath: str) -> "Pack":
        """
        Loads a backgrounds pack from the given JSON file.

        Parameters:
            filepath (str): Path to the JSON file to load.

        Returns:
            BackgroundPack: The loaded pack.
        """

        with open(filepath, "r", encoding="utf-8") as file:
            pack = json.load(file)
            pack["listCustomBackgrounds"] = [
                Background(**background)
                for background in pack["listCustomBackgrounds"]
            ]
        return Pack(**pack)


    def updated_from_background_sources(self, sources: list[BackgroundSource]):
        """
        Updates all backgrounds in the pack from the given sources.

        Parameters:
            sources (list[BackgroundSource]): List of BackgroundSource objects to search.

        Returns:
            None
        """
        background_sources = (
            (background, background.find_matching_source(sources))
            for background in self.listCustomBackgrounds
        )
        backgrounds = [
            source and background.updated_from_source(source) or background
            for background, source in background_sources
        ]
        if backgrounds == self.listCustomBackgrounds:
            return self

        return Pack(**(self.__dict__ | { "listCustomBackgrounds": backgrounds }))
