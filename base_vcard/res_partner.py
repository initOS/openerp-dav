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
from openerp.osv import orm
from .vcard_model import vcard_property
import vobject
from base64 import b64decode


class ResPartner(orm.Model):
    _inherit = ['res.partner', 'vcard.model']
    _name = 'res.partner'

    def _get_vcard_mapping(self):
        return super(ResPartner, self)._get_vcard_mapping() + \
            [vcard_property('email', column_name='email'),
             vcard_property('role', column_name='function'),
             vcard_property('note', column_name='comment'),
             vcard_property('url', column_name='website'),
             vcard_property('fn', column_name='name'),
             vcard_property('org', column_name='parent_id',
                            set_transformation=(lambda x: [x.name])),
             # list properties that are handled by _fill_get_vcard /
             #  _fill_set_vcard directly (so that we know which properties
             #  are NOT mapped by OpenERP)
             vcard_property('n'),
             vcard_property('adr'),
             vcard_property('tel'),
             vcard_property('photo'),
             ]

    def _fill_get_vcard(self, cr, uid, ids, vcard):
        partner_obj = self.browse(cr, uid, ids)[0]

        vcard.add('n')
        vcard.n.value = vobject.vcard.Name(family=partner_obj.name)
        if partner_obj.title:
            vcard.n.value.prefix = partner_obj.title.name

        # address = self.address_get(cr, uid, ids)
        address = partner_obj
        adr = vcard.add('adr')
        if not hasattr(adr, 'value'):
            adr.value = vobject.vcard.Address()
        adr.value.street = address.street and address.street + (
            address.street2 and (" " + address.street2) or '') or ''
        adr.value.city = address.city or ''
        if address.state_id:
            adr.value.region = address.state_id.name or ''
        adr.value.code = address.zip or ''
        if address.country_id:
            adr.value.country_id = address.country_id.name or ''

        if address.phone:
            tel = vcard.add('tel')
            tel.value = address.phone
            tel.type_param = 'work,voice'
        if address.mobile:
            tel = vcard.add('tel')
            tel.value = address.mobile
            tel.type_param = 'cell'
        if address.fax:
            tel = vcard.add('tel')
            tel.value = address.fax
            tel.type_param = 'work,fax'

        if partner_obj.image_small:
            vcard.add('photo')
            # vobject encodes the file for us
            vcard.photo.value = b64decode(partner_obj.image_small)
            vcard.photo.encoding_param = "B"
            vcard.photo.type_param = "PNG"

    def _fill_set_vcard(self, cr, uid, ids, vcard, update_values):
        partner_obj = self.browse(cr, uid, ids)[0]
        update_values = {}

        # a vcard MUST have an N and FN attribute, so we don't have to
        #  check whether these are available here

        if 'email' in vcard:
            for email in vcard['email']:
                if email.value != partner_obj.email:
                    update_values['email'] = email.value

        # update phone numbers
        if 'tel' in vcard:
            work_tel = [tel for tel in vcard['tel']
                            if u'work' in map(lambda x: x.lower(), tel.type_paramlist) and
                               u'fax' not in map(lambda x: x.lower(), tel.type_paramlist)]
            for tel in work_tel:
                if tel.value != partner_obj.phone:
                    update_values['phone'] = tel.value

            cell_tel = [tel for tel in vcard['tel']
                            if u'cell' in map(lambda x: x.lower(), tel.type_paramlist)]
            for tel in cell_tel:
                if tel.value != partner_obj.mobile:
                    update_values['mobile'] = tel.value
