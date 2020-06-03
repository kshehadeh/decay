import datetime
from typing import Union


class FileAnalysis(object):
    """
    File Analsysis object contains all the information that was retrieved during the analysis
    phase of document decay detection.  Reports are usually generated from this information as well
    as the aggregation of data from multiple instances of this object.
    """
    def __init__(self):
        self._file_link: str = ""
        self._file_identifier: str = ""
        self._file_changed_recently: bool = True
        self._last_change: Union[datetime.datetime, None] = None
        self._changed_by_email: Union[str, None] = None
        self._changed_by_name: Union[str, None] = None
        self._owner: str = ""
        self._doc_name: str = ""

    @property
    def file_link(self) -> str:
        return self._file_link

    @file_link.setter
    def file_link(self, val: str):
        self._file_link = val

    @property
    def changed_by_email(self) -> Union[str, None]:
        return self._changed_by_email

    @changed_by_email.setter
    def changed_by_email(self, val: Union[str, None]):
        self._changed_by_email = val

    @property
    def changed_by_name(self) -> Union[str, None]:
        return self._changed_by_name

    @changed_by_name.setter
    def changed_by_name(self, val: Union[str, None]):
        self._changed_by_name = val

    @property
    def last_change(self) -> Union[datetime.datetime, None]:
        return self._last_change

    @last_change.setter
    def last_change(self, val: Union[datetime.datetime, None]):
        self._last_change = val

    @property
    def file_identifier(self) -> str:
        return self._file_identifier

    @file_identifier.setter
    def file_identifier(self, val: str):
        self._file_identifier = val

    @property
    def doc_name(self) -> str:
        return self._doc_name

    @doc_name.setter
    def doc_name(self, val: str):
        self._doc_name = val

    @property
    def file_changed_recently(self) -> bool:
        return self._file_changed_recently

    @file_changed_recently.setter
    def file_changed_recently(self, val: bool):
        self._file_changed_recently = val

    @property
    def owner(self) -> str:
        return self._owner

    @owner.setter
    def owner(self, val: str):
        self._owner = val
