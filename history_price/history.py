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

class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """    
    _inherit = 'product.product'
    
    _columns = {
        'history_price': fields.boolean('Force price'),
        }
        
    _defaults = {
        'history_price': lambda *x: True,
        }

class PurchaseOrder(orm.Model):
    """ Model name: PurchaseOrder
    """    
    _inherit = 'purchase.order'
    
    def _force_price_product_order(self, cr, uid, ids, context=None):
        ''' Force procedure for update price in order
        '''
        assert len(ids) == 1, 'Works only with one record a time'
        
        suppinfo_pool = self.pool.get('product.supplierinfo')
        pricelist_pool = self.pool.get('pricelist.partnerinfo')
        
        order_proxy = self.browse(cr, uid, ids, context=context)[0]
        
        # No history for this order:
        if not order_proxy.history_price:
            return True
            
        for line in order.order_line:            
            # -----------------------------------------------------------------
            # Check supplier presence:
            # -----------------------------------------------------------------
            product = line.product_id
            if not product.history_price:
                return True # no history for this product
            
            seller_id = False
            price_id = False
            partner_id = order_proxy.partner_id.id
            for suppinfo in product.seller_ids
                if suppinfo.name.id == partner_id:
                    suppinfo_id = suppinfo.id # save seller supplierinfo id
                    for pl in suppinfo.pricelist_ids:
                        price_id = pl.id # XXX is the first present!!!
                        # TODO check quantity elements?
                    
            # ---------------------
            # Create if not present
            # ---------------------
            if not seller_id:    
                suppinfo_id = suppinfo_pool.create(cr, uid, {
                    'name': partner_id,
                    'product_id': product.id,
                    'sequence': 10,
                    'min_qty', 1.0,
                    'delay': 1
                    'product_uom', product.uom_id.id,                    
                    }, context=context)
            
            if price_id:
                pricelist_pool.write(cr, uid, price_id, {
                    'price': ,
                    #'min_quantity',
                    #'partner_id': seller_id, 
                    }, context=context)
            else:        
                pricelist_pool.create(cr, uid, {
                    'price': ,
                    'min_quantity': 1.0,
                    'suppinfo_id': suppinfo_id, 
                    }, context=context)
        return True
    
    _columns = {
        'history_price': fields.boolean('Force price'),
        }
        
    _defaults = {
        'history_price': lambda *x: True,
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
