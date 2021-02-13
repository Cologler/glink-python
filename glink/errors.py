# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------


class GLinkError(Exception):
    'the base error for glink'

    def __init__(self, message: str) -> None:
        self.message = message


class LocalFileRemovedError(GLinkError):
    pass


class RemoteFileRemovedError(GLinkError):
    pass


class ConflictError(GLinkError):
    pass


class MissingDataError(GLinkError):
    pass


class UnspecifiedUserError(GLinkError):
    pass
