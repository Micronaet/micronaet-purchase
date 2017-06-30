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

class StockMove(orm.Model):
    """ Model name: StockMove
    """    
    _inherit = 'stock.move'
    
    def reopen_sale_order(self, cr, uid, sol_proxy, context=None):
        '''
        ''' 
        # Pool used:
        sol_pool = self.pool.get('sale.order.line')
        order_pool = self.pool.get('sale.order')
        
        try:
            # Re-open order line:
            if sol_proxy.mx_closed:
                sol_pool.write(cr, uid, sol_proxy.id, {
                    'mx_closed': False,
                    }, context=context)
            # Re-open orer        
            if sol_proxy.order_id.mx_closed:
                order_pool.write(
                    cr, uid, sol_proxy.order_id.id, {
                        'mx_closed': False,
                        }, context=context)
        except:
            _logger.warning('Sale order line or order not reopened!')                
            return False
        return True    

    def force_unlink_button(self, cr, uid, ids, context=None):
        ''' Force unlink button
        '''
        assert len(ids) == 1, 'Only one a time'
        move_proxy = self.browse(cr, uid, ids, context=context)[0]

        log_file = os.path.expanduser('~/force_stock_move_delete.log')
        log_f = open(log_file, 'a')
        
        # Order closed problem:        
        self.reopen_sale_order(
            cr, uid, move_proxy.sale_line_id, context=context)
            
        log_message = '[Pick: %s] Force delete of: %s [%s] q. %s\n' % (
            move_proxy.picking_id.name or '',
            move_proxy.name,
            move_proxy.product_id.default_code,
            move_proxy.product_uom_qty,
            )
        _logger.warning(log_message)
        
        self.write(cr, uid, ids, {
            'state': 'cancel',
            }, context=context)
        self.unlink(cr, uid, ids, context=context)      
          
        log_f.write(log_message)
        log_f.close()
        return True
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
