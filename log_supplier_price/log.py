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

class PricelistPartnerinfo(orm.Model):
    ''' Add button event
    '''
    _inherit = 'pricelist.partnerinfo'
    
    # -------------
    # Button event:
    # -------------
    def open_history_price(self, cr, uid, ids, context=None):
        ''' Open history view
        '''        
        #view_id = self.pool.get('ir.ui.view').search(cr,uid,[
        #    ('model', '=', 'product.product.csv.import.wizard'),
        #    ('name', '=', 'Create production order') 
        #    ], context=context)
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'History price',
            'res_model': 'pricelist.partnerinfo',
            #'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'tree,form',
            #'view_id': view_id,
            'target': 'new',
            #'nodestroy': True,
            'domain': [('pricelist_id', '=', ids[0])],
            }
        
        
class PricelistPartnerinfoHistory(orm.Model):
    ''' Model name: PricelistPartnerinfoHistory
    '''
    
    _name = 'pricelist.partnerinfo.history'
    _description = 'Pricelist supplier history'
    _rec_name = 'pricelist_id'
    _order = 'date_quotation desc'
    
    _columns = {
        'date_quotation': fields.date('Date quotation'),
        'min_quantity': fields.integer('Min Q.'),
        'price': fields.float('Price'),
        'pricelist_id': fields.many2one(
            'pricelist.supplierinfo', 'Pricelist'),    
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
