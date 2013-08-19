# -*- coding: utf-8 -*-

"""
Copyright (C) 2013 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import logging
from traceback import format_exc

# anyjson
from anyjson import dumps

# Django
from django.http import HttpResponse, HttpResponseServerError

# Zato
from zato.admin.web import from_utc_to_user, from_user_to_utc, TARGET_TYPE_HUMAN
from zato.admin.web.forms.pattern.delivery import CreateForm, DeliveryTargetForm, EditForm, InstanceListForm
from zato.admin.web.views import CreateEdit, Delete as _Delete, Index as _Index, get_js_dt_format, method_allowed
from zato.common.model import DeliveryItem

logger = logging.getLogger(__name__)

class Index(_Index):
    method_allowed = 'GET'
    url_name = 'pattern-delivery'
    template = 'zato/pattern/delivery/definition/index.html'
    service_name = 'zato.pattern.delivery.definition.get-list'
    output_class = DeliveryItem
    
    class SimpleIO(_Index.SimpleIO):
        input_required = ('cluster_id', 'target_type')
        output_required = ('id', 'name', 'last_updated_utc', 'target', 'target_type', 
            'expire_after', 'expire_arch_succ_after', 'expire_arch_fail_after', 'check_after', 
            'retry_repeats', 'retry_seconds', 'short_def', 'total_count', 
            'in_progress_count', 'in_doubt_count', 'arch_success_count', 'arch_failed_count')
        output_repeated = True
        
    def on_before_append_item(self, item):
        if item.last_updated:
            item.last_updated = from_utc_to_user(item.last_updated_utc + '+00:00', self.req.zato.user_profile)
        return item
        
    def handle(self):
        target_type = self.req.GET.get('target_type')
        return {
            'delivery_target_form': DeliveryTargetForm(self.req.GET),
            'create_form': CreateForm(),
            'edit_form': EditForm(prefix='edit'),
            'target_type': target_type,
            'target_type_human': TARGET_TYPE_HUMAN[target_type] if target_type else '',
        }

class _CreateEdit(CreateEdit):
    method_allowed = 'POST'

    class SimpleIO(CreateEdit.SimpleIO):
        input_required = ['name', 'target', 'target_type', 'expire_after',
            'expire_arch_succ_after', 'expire_arch_fail_after', 'check_after', 
            'retry_repeats', 'retry_seconds']
        output_required = ['id', 'name', 'target', 'short_def']
        
class Create(_CreateEdit):
    url_name = 'pattern-delivery-create'
    service_name = 'zato.pattern.delivery.definition.create'
    
    def __call__(self, req, initial_input_dict={}, initial_return_data={}, *args, **kwargs):
        self.set_input(req)
        initial_return_data['target'] = self.input.target
        initial_return_data['short_def'] = '{}-{}-{}'.format(
            self.input.check_after, self.input.retry_repeats, self.input.retry_seconds)
        
        return super(Create, self).__call__(req, initial_input_dict, initial_return_data, args, kwargs)
    
    def success_message(self, item):
        return 'Definition [{}] created successfully'.format(item.name)
    
class Edit(_CreateEdit):
    url_name = 'pattern-delivery-edit'
    form_prefix = 'edit-'
    service_name = 'zato.pattern.delivery.definition.edit'

class Delete(_Delete):
    url_name = 'pattern-delivery-delete'
    error_message = 'Could not delete delivery'
    service_name = 'zato.pattern.delivery.definition.delete'