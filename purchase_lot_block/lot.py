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
        'purchase_lot_block': fields.integer('Purchase lot block'),
        }

class PurchaseOrderLine(orm.Model):
    """ Model name: PurchaseOrderLine
    """    
    _inherit = 'purchase.order.line'
        
    # Field function:
    def _get_puchase_lot_block(self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        res = {}
        
        for item in self.browse(cr, uid, ids, context=context):            
            res[item.id] = {'lot_info': '', 'lot_error': False}
            
            if item.product_id.is_pipe: 
                lot = item.product_id.pipe_min_order
            else:    
                lot = item.product_id.purchase_lot_block
                
            product_qty = item.product_qty
            if not lot or not product_qty:
                continue                

            if not product_qty % lot:
                status = 'OK'
            else:
                res[item.id]['lot_error'] = True
                minimum = product_qty // lot
                status = '[%s:%s]' % (
                    lot * minimum, 
                    lot * (minimum + 1),
                    )
            res[item.id]['lot_info'] = '%s %s' % (lot, status)
        return res
        
    _columns = {
        'lot_info': fields.function(
            _get_puchase_lot_block, method=True, 
            type='char', size=80, string='Lot', store=False, multi=True),

        'lot_error': fields.function(
            _get_puchase_lot_block, method=True, 
            type='boolean', string='Lot error', store=False, multi=True),
             
        }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
