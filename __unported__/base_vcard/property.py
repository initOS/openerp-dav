# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-2013 OpenERP s.a. (<http://openerp.com>).
#    Copyright (C) 2013-2014 initOS GmbH & Co. KG (<http://www.initos.com>).
#    Author Thomas Rehn <thomas.rehn at initos.com>
#    Author Markus Schneider <markus.schneider at initos.com>
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


class vcard_property(object):
    "Handles the connection between a vCard property and an OpenERP record"
    def __init__(self, vcard_name, column_name=None, set_transformation=None):
        self._vcard_name = vcard_name
        self._column_name = column_name
        self._set_transformation = set_transformation

    def vcard_name(self):
        return self._vcard_name

    def set_vcard(self, vcard, record):
        "Sets a vcard property from a browse object"
        if not self._column_name:
            return False
        record_val = getattr(record, self._column_name, None)
        if record_val and self._set_transformation:
            record_val = self._set_transformation(record_val)
        if record_val:
            vcard_prop = vcard.add(self._vcard_name)
            vcard_prop.value = record_val
            return True
        return False

    def get_vcard(self, update_values, vcard):
        """Reads a vcard property and puts in into a dictionary
           suitable for .write(.)"""
        if not self._column_name:
            return False
        if self._set_transformation:
            # getting attributes which have a set-transformation
            #  is not supported yet
            return False
        if self._vcard_name in vcard.contents:
            update_values[self._column_name] = \
                vcard.contents[self._vcard_name][0].value
            return True
        return False
