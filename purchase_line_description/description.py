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


class PurchaseOrderLine(orm.Model):
    """ Model name: PurchaseOrderLine
    """    
    _inherit = 'purchase.order.line'

    # Override onchange for update name
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, 
            uom_id, partner_id, date_order=False, fiscal_position_id=False, 
            date_planned=False, name=False, price_unit=False, state='draft', 
            context=None):
            
        res = super(PurchaseOrderLine, self).onchange_product_id(
            cr, uid, ids, pricelist_id, product_id, qty, 
            uom_id, partner_id, date_order=date_order, 
            fiscal_position_id=fiscal_position_id, date_planned=date_planned, 
            name=name, price_unit=price_unit, state=state, context=context)   
        
        line_proxy = self.browse(cr, uid, ids, context=context)[0]
        partner_id = line_proxy.partner_id.id
        product = line.product_id # readability

        for suppinfo in line_proxy.product_id.seller_ids:
            if suppinfo.name.id == partner_id:
                supp_name = '%s%s' % (
                    '[%s]' % suppinfo.product_code \
                        if suppinfo.product_code else '',
                    suppinfo.product_name or '',
                    )
                    
        name = '%s%s\n%s' % (
            '[%s]' % product.default_code if product.default_code else '',
            product.name or '',
            supp_name,
            )
        import pdb; pdb.set_trace()    
        return res    
       
            
        


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
