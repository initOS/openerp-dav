openerp-dav
===========

vCard and CardDAV modules for OpenERP (Odoo) v7 and v8

* base_vcard: This module introduces a vcard.model that helps to export and import OpenERP records as vCards. It includes a basic mapping for res.partner.
* crm_vcard: This module includes a basic mapping for crm.lead from and to vCards.
* document_carddav: A very simple CardDAV implementation
* document_webdav_fast: A copy of the original document_webdav module with patches for performance improvements.

*IMPORTANT* The modules require the latest version of PyWebDAV 0.9.8.
