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
    _inherit ='pricelist.partnerinfo'

    def _get_parent_information(self, cr, uid, ids, fields, args, 
            context=None):
        ''' Fields function for calculate all value used
        '''
        res = {}
        for price in self.browse(cr, uid, ids, context=context)[0]:
            # Readability:
            supplierinfo = price.suppinfo_id
            product = supplierinfo.product_tmpl_id # template!!
            
            res[price.id] = {            
                'supplier_id': supplierinfo.name.id, # partner ID
                'product_id': product.id,
                'product_supp_name': supplierinfo.product_name,
                'product_supp_code': supplierinfo.product_code,
                'product_name': product.name,
                'product_code': product.default_code,
                'uom_id': product.uom_id.id,
                }
        return res
        
    _columns = {
        'date_quotation': fields.date('Date quotation'), # TODO delete?
        'write_date': fields.datetime('Write date', readonly=True),
        
        # TODO change store?:
        'supplier_id': fields.function(
            _get_parent_information, method=True, 
            type='many2one', string='Supplier', relation='res.partner',
            store=True, multi=True),
        'product_id': fields.function( # XXX template
            _get_parent_information, method=True, store=True, multi=True,
            type='many2one', string='Product', relation='product.template'),
        'uom_id': fields.function(
            _get_parent_information, method=True, store=True, multi=True,
            type='many2one', string='UOM', relation='product.uom'),

        'product_supp_name': fields.function(
            _get_parent_information, method=True, store=True, multi=True,
            type='char', size=128, string='Supplier description'),
        'product_supp_code': fields.function(
            _get_parent_information, method=True, store=True, multi=True,
            type='char', size=64, string='Supplier code'),
        'product_name': fields.function(
            _get_parent_information, method=True, store=True, multi=True
            type='char', size=80, string='Company product'),
        'product_code': fields.function(
            _get_parent_information, method=True, store=True, multi=True
            type='char', size=20, string='Company code'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
