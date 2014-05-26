# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 initOS GmbH & Co. KG (<http://www.initos.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from threading import current_thread, Lock
import logging
_logger = logging.getLogger(__name__)


class CacheCursor(object):
    "Caches a triple per thread"

    def __init__(self):
        self._lock = Lock()
        self._cache = {}

    def _get_key(self):
        return repr(current_thread())

    def put(self, obj):
        with self._lock:
            self._cache[self._get_key()] = obj

    def get(self):
        with self._lock:
            return self._cache.get(self._get_key(), (None, None, None))

    def delete(self):
        with self._lock:
            key = self._get_key()
            if not key in self._cache:
                return
            del self._cache[self._get_key()]
