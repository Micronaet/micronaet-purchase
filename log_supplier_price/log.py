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
    ''' Add button event and override event
    '''
    _inherit = 'pricelist.partnerinfo'

    # --------------------------
    # Overide event for history:
    # --------------------------
    
    def write(self, cr, uid, ids, vals, context=None):
        """ Update redord(s) comes in {ids}, with new value comes as {vals}
            return True on success, False otherwise
            @param cr: cursor to database
            @param uid: id of current user
            @param ids: list of record ids to be update
            @param vals: dict of new values to be set
            @param context: context arguments, like lang, time zone
                > without_history: parameter
            
            @return: True on success, False otherwise            
        """
        if context is None:
            context = {}

        if type(ids) == int:
            ids = [ids]

        # Write anchestor procedure:
        res = super(PricelistPartnerinfo, self).write(
            cr, uid, ids, vals, context=context)

        if 'recursion' in context:
            return res
        # Browse current before update:
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        history_data = {
            'date_quotation': current_proxy.date_quotation,
            'min_quantity': current_proxy.min_quantity,
            'price': current_proxy.price,
            'pricelist_id': current_proxy.id,     
            }
            
        context['recursion'] = True
        
        no_history = context.get('without_history', False)
        if not no_history and 'price' in vals and len(ids) == 1:
            # Save history:
            history_pool = self.pool.get('pricelist.partnerinfo.history')
            history_pool.create(cr, uid, history_data, context=context)
        #res = super(PricelistPartnerinfo, self).write(
        #    cr, uid, ids, vals, context=context)
        return res   
    
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
        
        # TODO raise error if not present
        return {
            'type': 'ir.actions.act_window',
            'name': 'History price',
            'res_model': 'pricelist.partnerinfo.history',
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
        'price': fields.float('Price', digits=(8, 6)), # more decimal history
        'pricelist_id': fields.many2one(
            'pricelist.partnerinfo', 'Pricelist', ondelete='cascade'),
        
        # Show database fields:    
        'create_uid': fields.many2one(
            'res.users', 'History user'),
        'create_date': fields.date('Created'),
        }

class PricelistPartnerinfo(orm.Model):
    """ Model name: PricelistPartnerinfo
    """
    
    _inherit = 'pricelist.partnerinfo'
    
    _columns = {
        'history_ids': fields.one2many('pricelist.partnerinfo.history', 
            'pricelist_id', 'History'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
