# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################


import os
import sys
import logging
import openerp
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)


class StockMoveChangeQtyWizard(orm.TransientModel):
    ''' Wizard for change qty in stock move
    '''
    _name = 'stock.move.change.qty.wizard'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_change(self, cr, uid, ids, context=None):
        ''' Event for button done
        '''
        if context is None: 
            context = {}        

        log_file = os.path.expanduser('~/force_stock_move_delete.log')
        log_f = open(log_file, 'a')

        wiz_browse = self.browse(cr, uid, ids, context=context)[0]
        qty = wiz_browse.qty
        active_id = context.get('active_id')

        # Order closed problem:        
        move_pool = self.pool.get('stock.move')
        move_proxy = move_pool.browse(cr, uid, active_id, context=context)
        move_pool.reopen_sale_order(
            cr, uid, move_proxy.sale_line_id, context=context)
        
        # Change quantity:
        cr.execute('''
            UPDATE stock_move SET
                product_uom_qty = %s, product_uos_qty = %s, product_qty = %s
            WHERE id = %s;
            ''', (qty, qty, qty, active_id))
        
        # Open sale order line:
        cr.execute('''
            UPDATE sale_order_line 
            SET mx_closed = false
            WHERE id in (            
                SELECT sale_line_id 
                FROM stock_move 
                WHERE id = %s);
            ''', (active_id, ))
        
        # Open sale order:
        cr.execute('''
            UPDATE sale_order 
            SET mx_closed = 'f'
            WHERE id in (
                SELECT distinct order_id 
                FROM sale_order_line             
                WHERE id in (
                    SELECT sale_line_id 
                    FROM stock_move 
                    WHERE id = %s));
            ''', (active_id, ))
            
        # Log operations!
        log_message = 'stock_move ID %s product_uom_qty = %s (mx_closed)\n' % (
            active_id,
            qty
            )
        _logger.warning(log_message)    
        log_f.write(log_message)        
        log_f.close()
            
        return {
            'type': 'ir.actions.act_window_close'
            }

    _columns = {
        'qty': fields.float('New Qty', digits=(16, 4), required=True),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


