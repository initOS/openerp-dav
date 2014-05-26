# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.addons.document_webdav_fast import nodes
from openerp.addons.document_webdav_fast.dav_fs import dict_merge2
from openerp.addons.document.document import nodefd_static
from openerp.tools.safe_eval import safe_eval
import logging
_logger = logging.getLogger(__name__)


_NS_CARDDAV = "urn:ietf:params:xml:ns:carddav"


class node_model_vcard_collection(nodes.node_res_obj):
    "The children of this node are all models that implement vcard.model"

    def _get_default_node(self):
        return node_addressbook("default", self, self.context, 'res.partner')

    def _get_filter_nodes(self, cr):
        '''find all models that implement vcard.model'''
        fields_obj = self.context._dirobj.pool.get('ir.model.fields')
        fields_ids = fields_obj.search(cr, self.context.uid,
            [('name', '=', 'vcard_uid'),
             ('model_id.model', '!=', 'vcard.model')])
        fields = fields_obj.browse(cr, self.context.uid, fields_ids)
        return [node_filter("m-%s" % _field.model_id.model, self,
                                 self.context, _field.model_id.model,
                                 _field.model_id.name)
                for _field in fields]

    def _get_filter_nodes_by_name(self, cr, ir_model=None):
        model_obj = self.context._dirobj.pool.get('ir.model')
        model_ids = model_obj.search(cr, self.context.uid,
                                     [('model', '=', ir_model)])
        model_data = model_obj.read(cr, self.context.uid, model_ids,
                                   ['model', 'name'])
        return [node_filter("m-%s" % ir_model, self,
                                 self.context, str(ir_model),
                                 _model['name'])
                for _model in model_data]

    def _child_get(self, cr, name=False, parent_id=False, domain=None):
        if name:
            if name.startswith('m-'):
                return self._get_filter_nodes_by_name(cr, name[2:])
            return [self._get_default_node()]

        return [self._get_default_node()] + \
            self._get_filter_nodes(cr)


class node_filter(nodes.node_class):
    "The children of this node are all custom filters of a given model."
    DAV_M_NS = {
        "DAV:": '_get_dav',
    }

    def __init__(self, path, parent, context, ir_model='res.partner',
                 displayname=''):
        super(node_filter, self).__init__(path, parent, context)
        self.mimetype = 'application/x-directory'
        self.create_date = parent.create_date
        self.ir_model = ir_model
        self.displayname = displayname

    def _get_default_node(self):
        return node_addressbook("default", self, self.context, self.ir_model)

    def _get_filter_nodes(self, cr, filter_ids):
        filters_obj = self.context._dirobj.pool.get('ir.filters')
        filter_data = filters_obj.read(cr, self.context.uid, filter_ids,
                                       ['context', 'domain', 'name'])
        return [node_addressbook("filtered-%s" % _filter['id'], self,
                                 self.context,
                                 self.ir_model, _filter['name'],
                                 _filter['domain'], _filter['id'])
                for _filter in filter_data]

    def _get_ttag(self, cr):
        return 'addressbook-%d-%s' % (self.context.uid, self.ir_model)

    def get_dav_resourcetype(self, cr):
        return [('collection', 'DAV:')]

    def children(self, cr, domain=None):
        return self._child_get(cr, domain=domain)

    def child(self, cr, name, domain=None):
        res = self._child_get(cr, name, domain=domain)
        if res:
            return res[0]
        return None

    def _child_get(self, cr, name=False, parent_id=False, domain=None):
        if name:
            if name.startswith('filtered-'):
                return self._get_filter_nodes(cr, [int(name[9:])])
            return [self._get_default_node()]

        filters_obj = self.context._dirobj.pool.get('ir.filters')
        filter_ids = filters_obj.search(cr, self.context.uid,
            [('model_id', '=', self.ir_model),
             ('user_id', 'in', [self.context.uid, False])])
        return [self._get_default_node()] + \
            self._get_filter_nodes(cr, filter_ids)


class node_addressbook(nodes.node_class):
    """This node contains vCards for all records of a given model.
    If a filter is given, the node contains only those records
    that match the filter."""
    DAV_PROPS = dict_merge2(nodes.node_dir.DAV_PROPS,
                           {"DAV:": ('supported-report-set',),
                            _NS_CARDDAV: ('address-data',
                                          'supported-address-data',
                                          'max-resource-size',
                                          )})
    DAV_M_NS = {
                "DAV:": '_get_dav',
                _NS_CARDDAV: '_get_carddav',
                }
    http_options = {'DAV': ['addressbook']}

    def __init__(self, path, parent, context,
                 ir_model='res.partner', filter_name=None,
                 filter_domain=None, filter_id=None):
        super(node_addressbook, self).__init__(path, parent, context)
        self.mimetype = 'application/x-directory'
        self.create_date = parent.create_date
        self.ir_model = ir_model
        self.filter_id = filter_id
        if filter_domain and self.filter_id:
            self.filter_domain = ['|',
                                  ('dav_filter_id', '=', self.filter_id)] + \
                                  safe_eval(filter_domain)
        else:
            self.filter_domain = []
        if filter_name:
            self.displayname = "%s filtered by %s" % (ir_model, filter_name)
        else:
            self.displayname = "%s" % path
        # TODO self.write_date = max(create_date) [sic!] of all partners

    def children(self, cr, domain=None):
        if not domain:
            domain = []
        return self._child_get(cr, domain=(domain + self.filter_domain))

    def child(self, cr, name, domain=None):
        if not domain:
            domain = []
        res = self._child_get(cr, name, domain=(domain + self.filter_domain))
        if res:
            return res[0]
        return None

    def _child_get(self, cr, name=False, parent_id=False, domain=None):
        children = []
        res_partner_obj = self.context._dirobj.pool.get(self.ir_model)
        if not domain:
            domain = []

        if name:
            domain.append(('vcard_filename', '=', name))
        partner_ids = res_partner_obj.search(cr, self.context.uid, domain)

        for partner in res_partner_obj.browse(cr, self.context.uid,
                                              partner_ids):
            children.append(
                res_node_contact(partner.vcard_filename,
                                 self, self.context, partner,
                                 None, None, self.ir_model))
        return children

    def _get_ttag(self, cr):
        return 'addressbook-%d-%s' % (self.context.uid, self.path)

    def get_dav_resourcetype(self, cr):
        return [('collection', 'DAV:'),
                ('addressbook', _NS_CARDDAV)]

    def _get_dav_supported_report_set(self, cr):
        return ("supported-report", "DAV:",
                ("report", "DAV:",
                 [("addressbook-query", _NS_CARDDAV),
                  ("addressbook-multiget", _NS_CARDDAV)]))

    def _get_carddav_addressbook_description(self, cr):
        return self.displayname

    def _get_carddav_supported_addressbook_data(self, cr):
        return ('calendar-data', _NS_CARDDAV, None,
                    {'content-type': "text/vcard", 'version': "3.0"})

    def _get_carddav_max_resource_size(self, cr):
        return 65535

    def get_domain(self, cr, filter_node):
        '''
        Return a domain for the carddav filter

        :param cr: database cursor
        :param filter_node: the DOM Element of filter
        :return: a list for domain
        '''
        # TODO Check if some of the code of
        #  http://bazaar.launchpad.net/~aw/openerp-vertel/6.1/files/head:/carddav/
        #  can be recycled.
        #   webdav.py, _carddav_filter_domain()
        if not filter_node:
            return []
        if filter_node.localName != 'addressbook-query':
            return []

        raise ValueError("filtering is not implemented")

    def create_child(self, cr, path, data=None):
        if not data:
            raise ValueError("Cannot create a contact with no data")
        res_partner_obj = self.context._dirobj.pool.get(self.ir_model)
        uid = res_partner_obj.get_uid_by_vcard(data)
        partner_id = res_partner_obj.create(cr, self.context.uid,
                                            {'name': 'DUMMY_NAME',
                                             'vcard_uid': uid,
                                             'vcard_filename': path,
                                             'dav_filter_id': self.filter_id})
        res_partner_obj.set_vcard(cr, self.context.uid, [partner_id], data)
        partner = res_partner_obj.browse(cr, self.context.uid, partner_id)
        return res_node_contact(partner.vcard_filename, self, self.context,
                                partner, None, None, self.ir_model)


class res_node_contact(nodes.node_class):
    "This node represents a single vCard"
    our_type = 'file'
    DAV_PROPS = {
                 "urn:ietf:params:xml:ns:carddav": (
                    'addressbook-description',
                 )}

    DAV_PROPS_HIDDEN = {
                        "urn:ietf:params:xml:ns:carddav": (
                           'address-data',
                        )}

    DAV_M_NS = {
           "urn:ietf:params:xml:ns:carddav": '_get_carddav'}

    http_options = {'DAV': ['addressbook']}

    def __init__(self, path, parent, context, res_obj=None, res_model=None,
                 res_id=None, ir_model=None):
        super(res_node_contact, self).__init__(path, parent, context)
        self.mimetype = 'text/vcard; charset=utf-8'
        self.create_date = parent.create_date
        self.write_date = parent.write_date or parent.create_date
        self.displayname = None
        self.ir_model = ir_model

        self.res_obj = res_obj
        if self.res_obj:
            if self.res_obj.create_date:
                self.create_date = self.res_obj.create_date
            if self.res_obj.write_date:
                self.write_date = self.res_obj.write_date

    def open_data(self, cr, mode):
        return nodefd_static(self, cr, mode)

    def get_data(self, cr, fil_obj=None):
        return self.res_obj.get_vcard().serialize()

    def _get_carddav_address_data(self, cr):
        return self.get_data(cr)

    def get_dav_resourcetype(self, cr):
        return ''

    def get_data_len(self, cr, fil_obj=None):
        data = self.get_data(cr, fil_obj)
        if data:
            return len(data)
        return 0

    def set_data(self, cr, data):
        self.res_obj.set_vcard(data)

    def _get_ttag(self, cr):
        return 'addressbook-contact-%s-%d' % (self.res_obj._name,
                                              self.res_obj.id)

    def rm(self, cr):
        uid = self.context.uid
        partner_obj = self.context._dirobj.pool.get(self.ir_model)
        return partner_obj.unlink(cr, uid, [self.res_obj.id])


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4
