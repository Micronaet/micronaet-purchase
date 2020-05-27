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
import xlsxwriter # XLSX export
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

class PurchaseOrder(orm.Model):
    """ Model name: Purchase Order
    """
    
    _inherit = 'purchase.order'
    
    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
    def link_purchase_line_with_sale(self, cr, uid, ids, context=None):
        ''' Link all product with order open product 
        '''
        # Pool used:
        sol_pool = self.pool.get('sale.order.line')
        
        order = self.browse(cr, uid, ids, context=context)[0]
        
        # ---------------------------------------------------------------------
        # Track product total received in picking:
        # ---------------------------------------------------------------------
        res = {}
        product_ids = []
        for line in order.order_line:
            product = line.product_id
            default_code = product.default_code
            if default_code not in res:
                res[default_code] = [
                    0, # Total received
                    0, # Total open order
                    [], # SOL lines order
                    product, # Product
                    ]
                product_ids.append(product.id)

            res[default_code][0] += line.product_qty
            
        # ---------------------------------------------------------------------
        # Link sale order information:
        # ---------------------------------------------------------------------
        sol_ids = sol_pool.search(cr, uid, [
            # Only this product:
            ('product_id', 'in', product_ids),
            
            # In correct state:
            ('order_id.state', 'not in', ('cancel', 'draft', 'sent', 'done')),
            
            # Not marked as closed:
            ('mx_closed', '=', False),
            ('order_id.mx_closed', '=', False),
            ], context=context)
        for sol in sol_pool.browse(cr, uid, sol_ids, context=context):
            product = sol.product_id
            default_code = product.default_code            
            remain = sol.product_uom_qty - sol.delivered_qty
            if remain <= 0.0:
                continue

            res[default_code][1] += remain
            res[default_code][2].append(sol)
            
        # ---------------------------------------------------------------------
        # Generate file XLSX
        # ---------------------------------------------------------------------            
        excel_pool = self.pool.get('excel.writer')
        ws_name = 'Confronto ordini'
        excel_pool.create_worksheet(ws_name)

        # ---------------------------------------------------------------------
        # Formats
        # ---------------------------------------------------------------------            
        excel_pool.set_format()        
        f_header = excel_pool.get_format('header')
        f_text = excel_pool.get_format('text')
        f_number = excel_pool.get_format('number')

        # ---------------------------------------------------------------------
        # Setup col dimension:
        # ---------------------------------------------------------------------            
        excel_pool.column_width(ws_name, [
            15, 30, 20, 10, 10, 1, 15, 12, 30, 10])
        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            'PRODOTTO',
            'DESCRIZIONE',
            'COLORE',
            'ARRIVATO',
            'ORDINATO',
            '',
            'OC',
            'SCADENZA',
            'CLIENTE',
            'Q.',
            ], default_format=f_header)    

        # ---------------------------------------------------------------------
        # Prepare price last buy check
        # ---------------------------------------------------------------------
        for default_code, data in res.iteritems():
            row += 1
            received, order, sol, product = data
            
            # -----------------------------------------------------------------
            # Write data row::
            # -----------------------------------------------------------------
            excel_pool.write_xls_line(ws_name, row, [
                # Header:
                default_code,
                product.name,
                product.colour,
                (received, f_number),
                (order, f_number),                
                '',
                '',
                '',
                '',
                ('', f_number),
                ], default_format=f_text)
            
            # Order detail:
            if sol:
                row -= 1 # for write in the same line
                   
            for line in sol:
                row += 1
                excel_pool.write_xls_line(ws_name, row, [
                    line.order_id.name,
                    line.date_deadline or line.order_id.date_deadline or '',
                    line.order_id.partner_id.name, 
                    (line.product_uom_qty - line.delivered_qty, 
                        f_number)
                    ], default_format=f_text, col=6)
        return excel_pool.return_attachment(cr, uid, 'Confronto acquisti')

class StockPicking(orm.Model):
    """ Model name: StockPicking
    """
    
    _inherit = 'stock.picking'

    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
    def link_purchase_line_with_sale(self, cr, uid, ids, context=None):
        ''' Link all product with order open product 
        '''
        # Pool used:
        sol_pool = self.pool.get('sale.order.line')
        attachment_pool = self.pool.get('ir.attachment')
        
        picking = self.browse(cr, uid, ids, context=context)[0]
        
        # ---------------------------------------------------------------------
        # Track product total received in picking:
        # ---------------------------------------------------------------------
        res = {}
        product_ids = []
        for line in picking.move_lines:
            product = line.product_id
            default_code = product.default_code
            if default_code not in res:
                res[default_code] = [
                    0, # Total received
                    0, # Total open order
                    [], # SOL lines order
                    product, # Product
                    ]
                product_ids.append(product.id)

            res[default_code][0] += line.product_uom_qty
            
        # ---------------------------------------------------------------------
        # Link sale order information:
        # ---------------------------------------------------------------------
        sol_ids = sol_pool.search(cr, uid, [
            # Only this product:
            ('product_id', 'in', product_ids),
            
            # In correct state:
            ('order_id.state', 'not in', ('cancel', 'draft', 'sent', 'done')),
            
            # Not marked as closed:
            ('mx_closed', '=', False),
            ('order_id.mx_closed', '=', False),
            ], context=context)
        for sol in sol_pool.browse(cr, uid, sol_ids, context=context):
            product = sol.product_id
            default_code = product.default_code            
            remain = sol.product_uom_qty - sol.delivered_qty
            if remain <= 0.0:
                continue

            res[default_code][1] += remain
            res[default_code][2].append(sol)
            
        # ---------------------------------------------------------------------
        # Generate file XLSX
        # ---------------------------------------------------------------------            
        filename = '/tmp/check_purchase.xlsx'
        _logger.info('Extract: %s' % filename)
        WB = xlsxwriter.Workbook(filename)
        WS = WB.add_worksheet('Confronto ordini')

        # ---------------------------------------------------------------------
        # Formats
        # ---------------------------------------------------------------------            
        num_format = '#,##0'
        format_header = WB.add_format({
            'bold': True, 
            'font_color': 'black',
            'font_name': 'Courier 10 pitch', # 'Arial'
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#cfcfcf', # gray
            'border': 1,
            #'text_wrap': True,
            })
        format_text = WB.add_format({
            'font_color': 'black',
            'font_name': 'Courier 10 pitch',
            'font_size': 9,
            'align': 'left',
            'border': 1,
            })
        format_number = WB.add_format({
            'font_name': 'Courier 10 pitch',
            'font_size': 9,
            'align': 'right',
            'border': 1,
            'num_format': num_format,
            })

        # ---------------------------------------------------------------------
        # Setup col dimension:
        # ---------------------------------------------------------------------            
        WS.set_column('A:A', 15)
        WS.set_column('B:B', 30)
        WS.set_column('C:C', 20)
        WS.set_column('D:E', 10)
        WS.set_column('F:F', 1)
        WS.set_column('G:G', 15)
        WS.set_column('H:H', 12)
        WS.set_column('I:I', 30)
        WS.set_column('J:J', 10)
        WS.set_column('K:K', 10)

        # Header:
        counter = 0
        WS.write(counter, 0, 'PRODOTTO', format_header)
        WS.write(counter, 1, 'DESCRIZIONE', format_header)
        WS.write(counter, 2, 'COLORE', format_header)
        WS.write(counter, 3, 'ARRIVATO', format_header)
        WS.write(counter, 4, 'ORDINATO', format_header)
        WS.write(counter, 5, '', format_header)
        WS.write(counter, 6, 'OC', format_header)
        WS.write(counter, 7, 'SCADENZA', format_header)
        WS.write(counter, 8, 'CLIENTE', format_header)
        WS.write(counter, 9, 'Q.', format_header)

        # ---------------------------------------------------------------------
        # Prepare price last buy check
        # ---------------------------------------------------------------------
        for default_code, data in res.iteritems():
            counter += 1
            received, order, sol, product = data
            
            # -----------------------------------------------------------------
            # Write data row::
            # -----------------------------------------------------------------
            # Header:
            WS.write(counter, 0, default_code, format_text)
            WS.write(counter, 1, product.name, format_text)
            WS.write(counter, 2, product.colour, format_text)
            WS.write(counter, 3, received, format_number)
            WS.write(counter, 4, order, format_number)
            
            # Order detail:
            if sol: 
                counter -= 1 # for write in the same line
            else:
                WS.write(counter, 6, '', format_text)
                WS.write(counter, 7, '', format_text)
                WS.write(counter, 8, '', format_text)
                WS.write(counter, 9, '', format_number)
                   
            for line in sol:
                counter += 1
                WS.write(counter, 6, line.order_id.name, format_text)
                WS.write(
                    counter, 7, 
                    line.date_deadline or line.order_id.date_deadline or '', 
                    format_text)
                
                WS.write(counter, 8, line.order_id.partner_id.name, 
                    format_text)
                WS.write(counter, 9, 
                    line.product_uom_qty - line.delivered_qty, 
                    format_number)
        WB.close()

        # ---------------------------------------------------------------------
        # Return XLSX file:
        # ---------------------------------------------------------------------
        b64 = open(filename, 'rb').read().encode('base64')
        attachment_id = attachment_pool.create(cr, uid, {
            'name': _('Confronto ricezione ordinato'),
            'datas_fname': 'confronto_ricezione_ordinato.xlsx',
            'type': 'binary',
            'datas': b64,
            #'partner_id': 1,
            'res_model': 'res.partner',
            'res_id': 1,
            }, context=context)
            
        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/binary/saveas?model=ir.attachment&field=datas&'
                'filename_field=datas_fname&id=%s' % attachment_id,
            'target': 'self',
            }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
