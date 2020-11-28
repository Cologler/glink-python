# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import hashlib

def sha1_bytes(buffer: bytes):
    return hashlib.sha1(buffer).hexdigest()
