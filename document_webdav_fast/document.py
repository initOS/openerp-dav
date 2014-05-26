# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import orm
from .cache import memoize
from openerp.addons.document.document import node_context


class document_directory(orm.Model):
    _inherit = 'document.directory'

    def get_object(self, cr, uid, uri, context=None):
        """ Return a node object for the given uri.
           This fn merely passes the call to node_context
        """
        return get_node_context_fast(cr, uid, context).get_uri(cr, uri)


@memoize(20000)
def get_node_context_fast(cr, uid, context):
    return node_context_fast(cr, uid, context)


class node_context_fast(node_context):
    def __init__(self, cr, uid, context=None):
        super(node_context_fast, self).__init__(cr, uid, context=context)
        self._cache = {}

    def get_uri(self, cr, uri):
        """ Although this fn passes back to doc.dir, it is needed since
            it is a potential caching point.
        """
        uri = map(unicode, uri)
        (ndir, duri) = (None, None)
        for i in range(len(uri), 1, -1):
            _key = (repr(cr), repr(uri[:i]))
            if _key in self._cache:
                ndir = self._cache[_key]
                duri = uri[i:]
                break
        if not ndir:
            (ndir, duri) =  self._dirobj._locate_child(cr, self.uid, self.rootdir, uri, None, self)
        for i in range(len(duri)):
            ndir = ndir.child(cr, duri[i])
            if not ndir:
                return False
            _key = (repr(cr), repr(duri[:(i + 1)]))
            self._cache[_key] = ndir
        return ndir
