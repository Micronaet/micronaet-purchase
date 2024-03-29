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
    ''' Add last price in product list
    '''
    _inherit = 'product.product'
    
    # Fields function:
    def _get_last_price_information(self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = {
                'last_price_price': 0.0,
                'last_price_date': False,
                'last_price_supplier': False,
                'last_price_active': 0,
                'last_price_unactive': 0,
                }
            for supplier in product.seller_ids:            
                for price in supplier.pricelist_ids:
                    if not price.is_active: 
                        res[product.id]['last_price_unactive'] += 1
                        continue
                    res[product.id]['last_price_active'] += 1
                    if not res[product.id]['last_price_date'] or \
                             res[product.id]['last_price_date'] < \
                                price.date_quotation:
                        res[product.id].update({
                            'last_price_price': price.price,
                            'last_price_date': price.date_quotation,
                            'last_price_supplier': supplier.name.id,
                            })
        return res

    _columns = {    
        'last_price_price': fields.function(
            _get_last_price_information, method=True, 
            type='float', string='Ultimo prezzo', multi=True, digits=(20, 5),
            ),
        'last_price_date': fields.function(
            _get_last_price_information, method=True, 
            type='date', string='Ultima data', multi=True), 
        'last_price_supplier': fields.function(
            _get_last_price_information, method=True, 
            type='many2one', string='Fornitore', relation='res.partner', 
            multi=True), 
        'last_price_unactive': fields.function(
            _get_last_price_information, method=True, 
            type='integer', string='# Disatt.', multi=True), 
        'last_price_active': fields.function(
            _get_last_price_information, method=True, 
            type='integer', string='# Attivi', multi=True), 
        }                    
class PricelistPartnerinfo(orm.Model):
    ''' Add button event and override event
    '''
    _inherit = 'pricelist.partnerinfo'

    # --------------------------
    # Override event for history:
    # --------------------------
    def write(self, cr, uid, ids, vals, context=None):
        """Update redord(s) comes in {ids}, with new value comes as {vals}
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

        # Browse current before update:
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        history_data = {
            'date_quotation': current_proxy.date_quotation,
            'min_quantity': current_proxy.min_quantity,
            'price': current_proxy.price,
            'pricelist_id': current_proxy.id,     
            }
            
        if 'price' in vals and len(ids) == 1:
            # Save history:
            history_pool = self.pool.get('pricelist.partnerinfo.history')
            history_pool.create(cr, uid, history_data, context=context)
            _logger.warning('Update history price: %s' % vals['price'])

        return super(PricelistPartnerinfo, self).write(
            cr, uid, ids, vals, context=context)

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
    
    def _get_original_product_id(self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.pricelist_id.product_id.id
        return res
            
    _columns = {
        'date_quotation': fields.date('Date quotation'),
        'min_quantity': fields.integer('Min Q.'),
        'price': fields.float('Price', digits=(8, 6)), # more decimal history
        # todo price_original (per le modifiche)
        
        'pricelist_id': fields.many2one(
            'pricelist.partnerinfo', 'Pricelist', ondelete='cascade'),
        'product_id': fields.function(
            _get_original_product_id, method=True, 
            type='many2one', string='Prodotto', relation='product.product',
            store=False),                         
        
        # Show database fields:    
        'create_uid': fields.many2one(
            'res.users', 'History user'),
        'create_date': fields.date('Created'),
        }

class PricelistPartnerinfoExtra(orm.Model):
    """ Model name: PricelistPartnerinfo
    """
    
    _inherit = 'pricelist.partnerinfo'
    
    _columns = {
        'history_ids': fields.one2many('pricelist.partnerinfo.history', 
            'pricelist_id', 'History'),
        }

