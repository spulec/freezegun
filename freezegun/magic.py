#!/usr/bin/env python
# -*- coding: utf-8 -*-
# <sure - utility belt for automated testing in python>
# Copyright (C) <2012>  Gabriel Falcão <gabriel@nacaolivre.org>
# Copyright (C) <2012>  Lincoln Clarete <lincoln@comum.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

import platform

is_cpython = (
    hasattr(platform, 'python_implementation')
    and platform.python_implementation().lower() == 'cpython')

if is_cpython:

    import ctypes
    DictProxyType = type(object.__dict__)

    Py_ssize_t = \
        hasattr(ctypes.pythonapi, 'Py_InitModule4_64') \
            and ctypes.c_int64 or ctypes.c_int

    class PyObject(ctypes.Structure):
        pass

    PyObject._fields_ = [
        ('ob_refcnt', Py_ssize_t),
        ('ob_type', ctypes.POINTER(PyObject)),
    ]

    class SlotsProxy(PyObject):
        _fields_ = [('dict', ctypes.POINTER(PyObject))]

    def patchable_builtin(klass):
        name = klass.__name__
        target = getattr(klass, '__dict__', name)

        if not isinstance(target, DictProxyType):
            return target

        proxy_dict = SlotsProxy.from_address(id(target))
        namespace = {}

        ctypes.pythonapi.PyDict_SetItem(
            ctypes.py_object(namespace),
            ctypes.py_object(name),
            proxy_dict.dict,
        )

        return namespace[name]
else:
    patchable_builtin = lambda *args, **kw: None
