#|/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
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

class PurchaseOrderLabelReportWizard(orm.TransientModel):
    ''' Form to select type of print
    '''
    _name = 'purchase.order.label.report.wizard'
    _description = 'Label report wizard'

    _columns = {
        'label_1': fields.boolean('Label 1'),
        'label_2': fields.boolean('Label 2'),
        'label_3': fields.boolean('Label 3'),
        'label_4': fields.boolean('Label 4'),
        'label_5': fields.boolean('Label 5'),
        'label_6': fields.boolean('Label 6'),
        }

    _defaults = {
        'label_1': lambda *x: True,
        'label_2': lambda *x: True,
        'label_3': lambda *x: True,
        'label_4': lambda *x: True,
        'label_5': lambda *x: True,
        'label_6': lambda *x: True,
        }

    def print_report(self, cr, uid, ids, context=None):
        ''' Print report passing parameter dictionary
        '''
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        datas = {}
        datas['label_1'] = wiz_proxy.label_1
        datas['label_2'] = wiz_proxy.label_2
        datas['label_3'] = wiz_proxy.label_3
        datas['label_4'] = wiz_proxy.label_4
        datas['label_5'] = wiz_proxy.label_5
        datas['label_6'] = wiz_proxy.label_6

        return {
            'model': 'purchase.order',
            'type': 'ir.actions.report.xml',
            'report_name': 'purchase_label_report',
            'datas': datas,
            #'res_id': context.get('active_id', False),
            #'context': context, #{'active_id':context.get('active_id', False), 'active_ids': context.get('active_ids', [])},#context,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
