# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-2014 initOS GmbH & Co. KG (<http://www.initos.com>).
#    Author Thomas Rehn <thomas.rehn at initos.com>
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

from openerp.osv import orm, fields
from .carddav_node import node_model_vcard_collection


class AddressbookCollection(orm.Model):
    _inherit = 'document.directory'

    _columns = {
        'addressbook_collection': fields.boolean('Addressbook Collection'),
    }

    _default = {
        'addressbook_collection': False,
    }

    def get_node_class(self, cr, uid, ids, dbro=None, dynamic=False,
                       context=None):
        if dbro is None:
            dbro = self.browse(cr, uid, ids, context=context)

        if dbro.addressbook_collection:
            return node_model_vcard_collection
        else:
            return super(AddressbookCollection, self) \
                .get_node_class(cr, uid, ids, dbro=dbro, dynamic=dynamic,
                                context=context)

    def get_description(self, cr, uid, ids, context=None):
        # TODO : return description of all calendars
        return False


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
