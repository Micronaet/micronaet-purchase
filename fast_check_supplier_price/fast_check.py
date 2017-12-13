# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class PricelistPartnerinfoExtraFields(orm.Model):
    ''' Add related fields
    '''
    _inherit = 'pricelist.partnerinfo'

    def update_all_partnerinfo_information(self, cr, uid, ids, context=None):
        ''' Force all procedure
        '''        
        product_pool = self.pool.get('product.product')        
        product_ids = product_pool.search(cr, uid, [], context=context)
        for product in product_pool.browse(cr, uid, product_ids, context=context):
            if not product.seller_ids:
                continue
            # force regeneration with saving same default_code
            product_pool.write(cr, uid, product.id, {
                'default_code': product.default_code, 
                }, context=context)        
        return True

    def get_parent_information(self, cr, uid, ids, fields, args, 
            context=None):
        ''' Fields function for calculate all value used
        '''
        _logger.warning('Update price # %s' % len(ids))        
        product_pool = self.pool.get('product.product')        
        
        res = {}
        for price in self.browse(cr, uid, ids, context=context):        
            # Readability:
            supplierinfo = price.suppinfo_id
            template = supplierinfo.product_tmpl_id # template!!
            product_ids = product_pool.search(cr, uid, [
                ('product_tmpl_id', '=', template.id),
                ], context=context)
            if product_ids:
                product_id = product_ids[0]
                default_code = product_pool.browse(
                    cr, uid, product_id, context=context).default_code
            else:    
                product_id = False
                default_code = False

            res[price.id] = {  
                # Key:
                'supplier_id': supplierinfo.name.id, # Partner ID
                'product_id': product_id,
                'uom_id': template.uom_id.id,

                # Supplier:
                'product_supp_name': supplierinfo.product_name,
                'product_supp_code': supplierinfo.product_code,

                # Product:
                'product_name': template.name,
                'product_code': default_code,
                }                
        return res

    # -------------------------------------------------------------------------    
    # reload function:
    # ------------------------------------------------------------------------- 
    # product.supplierinfo:   
    def _reload_price_supplier_id_product_code_and_name(
            self, cr, uid, ids, context=None):
        ''' Price change:
            product.supplierinfo  >> product_code and product_name
        '''
        _logger.warning('product.supplierinfo | partner_code or partner_name')
        item_ids = self.pool.get('pricelist.partnerinfo').search(cr, uid, [
            ('suppinfo_id', 'in', ids),
            ], context=context)

        _logger.warning('Change price: %s' % (item_ids, ))
        return item_ids    

    # product.product:
    def _reload_price_product_id_code(
            self, cr, uid, ids, context=None):
        ''' Price change:
            product.product  >> default_code
        '''
        _logger.warning('product.product > default_code')
        seller_ids = []
        
        # Search all seller for refresh:        
        for product in self.browse(cr, uid, ids, context=context):
            seller_ids.extend([item.id for item in product.seller_ids])
        _logger.warning('Change name or code >> seller_ids:  %s' % (
            seller_ids, ))
        
        # Refresh price for all seller:
        item_ids = self.pool.get('pricelist.partnerinfo').search(cr, uid, [
            ('suppinfo_id', 'in', seller_ids),
            ], context=context)
        _logger.warning('Change price: %s' % (item_ids, ))
        return item_ids
    
    # product.template:
    def _reload_price_product_id_name(
            self, cr, uid, ids, context=None):
        ''' Price change:
            product.template  >> name
        '''
        _logger.warning('product.template > name')
        seller_ids = []

        # Search product from template:        
        product_ids = self.pool.get('product.product').search(cr, uid, [
            ('product_tmpl_id', 'in', ids)], context=context)
        _logger.warning('Template name: product: %s' % (product_ids, ))

        # Search all seller for refresh:
        import pdb; pdb.set_trace()
        for product in self.browse(cr, uid, product_ids, context=context):
            seller_ids.extend([item.id for item in product.seller_ids])
        _logger.warning('Product seller >> seller_ids: %s' % (
            seller_ids, ))
        
        # Refresh price for all seller:
        item_ids = self.pool.get('pricelist.partnerinfo').search(cr, uid, [
            ('suppinfo_id', 'in', seller_ids),
            ], context=context)
        _logger.warning('Change price: %s' % (item_ids, ))
        return item_ids    
     
    def _reload_current_pricelist_forced(self, cr, uid, ids, context=None):
        ''' Force this
        '''
        _logger.warning('Force current: %s' % ids)
        return ids
        
    _columns = {
        'force': fields.boolean('Force related data'),
        'date_quotation': fields.date('Date quotation'), # TODO delete?
        'write_date': fields.datetime('Write date', readonly=True),
        
        # Fixed ref:
        'supplier_id': fields.function(
            get_parent_information, method=True, 
            type='many2one', string='Supplier', relation='res.partner',
            multi=True,
            # Used to force data, not real store function:
            store = {
                'pricelist.partnerinfo': (
                    _reload_current_pricelist_forced, ['force'], 10),
                'product.product': (
                    _reload_price_product_id_code, 
                    ['default_code'], 10),
                }),
        'product_id': fields.function( # XXX template
            get_parent_information, method=True, multi=True,
            type='many2one', string='Product', relation='product.product',
            # Used to force data, not real store function:
            store = {
                'pricelist.partnerinfo': (
                    _reload_current_pricelist_forced, ['force'], 10),
                'product.product': (
                    _reload_price_product_id_code, 
                    ['default_code'], 10),
                }),
        'uom_id': fields.function(
            get_parent_information, method=True, multi=True,
            type='many2one', string='UOM', relation='product.uom',
            store = {
                'pricelist.partnerinfo': (
                    _reload_current_pricelist_forced, ['force'], 10),
                # Used to force data, not real store function:
                'product.product': (
                    _reload_price_product_id_code, 
                    ['default_code'], 10),
                # TODO add extra store
            }),

        # Supplier:
        'product_supp_name': fields.function(
            get_parent_information, method=True, multi=True,
            type='char', size=128, string='Supplier description',
            store = {
                'pricelist.partnerinfo': (
                    _reload_current_pricelist_forced, ['force'], 10),
                'product.supplierinfo': (
                    _reload_price_supplier_id_product_code_and_name, 
                    ['product_name'], 10),
                # Used to force data, not real store function:
                'product.product': (
                    _reload_price_product_id_code, 
                    ['default_code'], 10),
                }),            
        'product_supp_code': fields.function(
            get_parent_information, method=True, multi=True,
            type='char', size=64, string='Supplier code',
            store = {
                'pricelist.partnerinfo': (
                    _reload_current_pricelist_forced, ['force'], 10),
                'product.supplierinfo': (
                    _reload_price_supplier_id_product_code_and_name, 
                    ['product_code'], 10),
                # Used to force data, not real store function:
                'product.product': (
                    _reload_price_product_id_code, 
                    ['default_code'], 10),
                }),

        # Product:
        'product_name': fields.function(
            get_parent_information, method=True, multi=True,
            type='char', size=80, string='Company product',
            store = {
                'pricelist.partnerinfo': (
                    _reload_current_pricelist_forced, ['force'], 10),
                'product.template': (
                    _reload_price_product_id_name, 
                    ['name'], 10),
                # Used to force data, not real store function:
                'product.product': (
                    _reload_price_product_id_code, 
                    ['default_code'], 10),
                }),
        'product_code': fields.function(
            get_parent_information, method=True, multi=True,
            type='char', size=20, string='Company code',
            store = {
                'pricelist.partnerinfo': (
                    _reload_current_pricelist_forced, ['force'], 10),
                'product.product': (
                    _reload_price_product_id_code, 
                    ['default_code'], 10),
                }),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
