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

from openerp.osv import orm, fields
from .property import vcard_property
import uuid
import vobject
try:
    import cPickle as pickle
except ImportError:
    import pickle


class vcard_model(orm.AbstractModel):
    """This class can be used as a mix-in to import and export
     existing models as vCards and to make models availabel as
     a CardDAV addressbook"""

    _name = 'vcard.model'
    _description = 'Card Model'

    _columns = {
        'create_date': fields.datetime('Creation date', readonly=True),
        'write_date': fields.datetime('Last Update', readonly=True),
        'vcard_uid': fields.char('UID for vCard', size=128, required=True,
                               select=True),
        'vcard_filename': fields.char('Filename of vCard', size=128,
                                    required=True, select=True),
        'vcard_properties': fields.binary('Additional vCard Properties '
                                          '(not managed by OpenERP)'),
        'dav_filter_id': fields.many2one('ir.filters',
                                         'Filter that the record '
                                         'was created under'),
    }

    _defaults = {
        'vcard_uid': lambda *x: uuid.uuid4(),
        'vcard_filename': lambda *x: str(uuid.uuid4()) + '.vcf',
    }

    _sql_constraints = [
        ('vcard_uid_uniq', 'unique(vcard_uid)',
         'CardDAV UID must be unique in a database'),
        ('vcard_filename_uniq', 'unique(vcard_filename)',
         'CardDAV file name must be unique in a database'),
    ]

    def copy(self, cr, uid, _id, default=None, context=None):
        default = default or {}
        # - set a new uid on copy
        # - don't copy unmapped vCard properties
        default.update({
            'vcard_uid': str(uuid.uuid4()),
            'vcard_filename': str(uuid.uuid4()) + '.vcf',
            'vcard_properties': False,
        })
        return super(vcard_model, self).copy(cr, uid, _id, default,
                                             context=context)

    def _get_vcard_mapping(self):
        "Defines mapping between vCard and model properties"
        return [vcard_property('uid', column_name='vcard_uid'),
                vcard_property('rev', column_name='write_date',
                               set_transformation=(lambda x: x.replace(' ', 'T') + 'Z'))]

    def _fill_get_vcard(self, cr, uid, ids, vcard):
        """Called if a vCard has to be generated from a model.
        This method can be used to extend the mapping mechanism provided by
        _get_vcard_mapping"""
        pass

    def _fill_set_vcard(self, cr, uid, ids, vcard, update_values):
        """Called if a model is to be created/updated from a vCard.
        This method can be used to extend the mapping mechanism provided by
        _get_vcard_mapping."""
        pass

    def get_vcard(self, cr, uid, ids):
        "Exports a model as a vCard"
        record = self.browse(cr, uid, ids)[0]

        vcard = vobject.vCard()
        mapped_properties = set()
        for prop in self._get_vcard_mapping():
            prop.set_vcard(vcard, record)
            mapped_properties.add(prop.vcard_name())

        unmapped_properties = []
        if record.vcard_properties:
            unmapped_properties = pickle.loads(record.vcard_properties)
        for prop in unmapped_properties:
            if prop.name.lower() not in mapped_properties:
                vcard.add(prop)

        self._fill_get_vcard(cr, uid, ids, vcard)
        return vcard

    def set_vcard(self, cr, uid, ids, vcard_string):
        "Import a model from a vCard"
        vcard = vobject.readOne(vcard_string)

        mapped_properties = set(['version'])
        update_values = {}
        for prop in self._get_vcard_mapping():
            prop.get_vcard(update_values, vcard)
            mapped_properties.add(prop.vcard_name())

        unmapped_properties = []
        for prop in vcard.getChildren():
            if prop.name.lower() not in mapped_properties:
                unmapped_properties.append(prop)
        update_values['vcard_properties'] = \
            pickle.dumps(unmapped_properties)

        self._fill_set_vcard(cr, uid, ids, vcard.contents, update_values)
        self.write(cr, uid, ids, update_values)

    def get_uid_by_vcard(self, vcard_string):
        vcard = vobject.readOne(vcard_string)
        return vcard.uid.value

    def _migrate_vcard_uid(self, cr, uid, ids=None, context=None):
        # We overwrite existing uids because of the following behavior
        #  of OpenERP: When a new column with default value is added,
        #  this default value is only computed once. Therefore
        #  all rows share the same vcard_uid.
        cr.execute("""UPDATE %s
                         SET vcard_uid = 'internal-' || id,
                             vcard_filename = 'internal-' || id || '.vcf' """
                   % (self._table))
        # After we fixed the uids, we can add the unique constraint
        #  if it not already exists (if the database contained less than
        #  two users, the uid was unique before).
        for col_name in ["vcard_uid", "vcard_filename"]:
            constraint_name = "%s_%s_uniq" % (self._table, col_name)
            cr.execute("""SELECT conname,
                                 pg_catalog.pg_get_constraintdef(oid, true)
                                   AS condef
                            FROM pg_constraint
                           WHERE conname=%s""", (constraint_name,))
            if not cr.fetchone():
                cr.execute("""ALTER TABLE "%s" ADD CONSTRAINT "%s" %s"""
                           % (self._table, constraint_name,
                              "UNIQUE(%s)" % col_name))
