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
{
    "name": "CardDAV",
    "version": "0.1",
    "depends": ["base", "document_webdav_fast", "web",
                "base_vcard", "crm_vcard"],
    'author': 'initOS GmbH & Co. KG',
    "category": "",
    "summary": "A simple CardDAV implementation",
    'license': 'AGPL-3',
    "description": """
A very simple CardDAV implementation
====================================

Urls:

- For all partners: /webdav/$db_name/addressbooks/users/$login/a-res.partner/default/
- For all leads: /webdav/$db_name/addressbooks/users/$login/a-crm.lead/default/

Collections can be filtered, the url is then shown in the search view drop-down.
    """,
    'data': [
        'carddav_setup.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'js': ['static/src/js/search.js'],
    'qweb': ['static/src/xml/base.xml'],
}
