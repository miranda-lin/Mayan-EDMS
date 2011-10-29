from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.views.generic.list_detail import object_list
from django.core.urlresolvers import reverse
from django.views.generic.create_update import create_object, delete_object, update_object
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist

from permissions.api import check_permissions, namespace_titles, get_permission_label, get_permission_namespace_label
from common.utils import generate_choices_w_labels, encapsulate
from common.widgets import two_state_template

from acls import ACLS_EDIT_ACL, ACLS_VIEW_ACL
from acls.models import AccessEntry, AccessObject, AccessHolder
from acls.widgets import object_w_content_type_icon


def _permission_titles(permission_list):
    return u', '.join([get_permission_label(permission) for permission in permission_list])
    
    
def acl_list_for(request, obj, extra_context=None):
    #check_permissions(request.user, [ACLS_VIEW_ACL])

    ct = ContentType.objects.get_for_model(obj)

    context = {
        #'app_label': ct.app_label,
        #'model_name': ct.model,
        'object_list': AccessEntry.objects.get_holders_for(obj),
        'title': _(u'access control lists for: %s' % obj),
        #'multi_select_as_buttons': True,
        #'hide_links': True,
        'extra_columns': [
            #{'name': _(u'holder'), 'attribute': 'label'},
            #{'name': _(u'obj'), 'attribute': 'holder_object'},
            #{'name': _(u'gid'), 'attribute': 'gid'},
            {'name': _(u'holder'), 'attribute': encapsulate(lambda x: object_w_content_type_icon(x.source_object))},
            {'name': _(u'permissions'), 'attribute': encapsulate(lambda x: _permission_titles(AccessEntry.objects.get_permissions_for_holder(obj, x.source_object)))},
            #{'name': _(u'arguments'), 'attribute': 'arguments'}
            ],
        #'hide_link': True,
        'hide_object': True,
        'access_object': AccessObject.encapsulate(obj)
    }

    if extra_context:
        context.update(extra_context)

    return render_to_response('generic_list.html', context,
        context_instance=RequestContext(request))	


def acl_list(request, app_label, model_name, object_id):
    ct = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    obj = get_object_or_404(ct.get_object_for_this_type, pk=object_id)
    return acl_list_for(request, obj)


def acl_detail(request, access_object_gid, holder_object_gid):
    #check_permissions(request.user, [ACLS_VIEW_ACL, ACLS_EDIT_ACL])
    
    try:
        holder = AccessHolder.get(gid=holder_object_gid)
        access_object = AccessObject.get(gid=access_object_gid)
    except ObjectDoesNotExist:
        raise Http404
        
    permission_list = list(set(AccessEntry.objects.get_permissions_for_holder(access_object.source_object, request.user)))
    #TODO : get all globalluy assignes permission, new function get_permissions_for_holder (roles aware)
    subtemplates_list = [
        {
            'name': u'generic_list_subtemplate.html',
            'context': {
                'title': _(u'permissions held by: %s for %s' % (holder, access_object)),
                'object_list': permission_list,
                'extra_columns': [
                    {'name': _(u'namespace'), 'attribute': encapsulate(lambda x: get_permission_namespace_label(x))},
                    {'name': _(u'name'), 'attribute': encapsulate(lambda x: get_permission_label(x))},
                    {
                        'name':_(u'has permission'),
                        'attribute': encapsulate(lambda x: two_state_template(AccessEntry.objects.has_accesses(x, holder.source_object, access_object.source_object)))
                    },
                ],
                #'hide_link': True,
                'hide_object': True,
            }
        },
    ]

    return render_to_response('generic_detail.html', {
        #'form': form,
        'object': access_object.obj,
        'subtemplates_list': subtemplates_list,
        #'multi_select_as_buttons': True,
        #'multi_select_item_properties': {
        #    'permission_id': lambda x: x.pk,
        #    'requester_id': lambda x: role.pk,
        #    'requester_app_label': lambda x: ContentType.objects.get_for_model(role).app_label,
        #    'requester_model': lambda x: ContentType.objects.get_for_model(role).model,
        #},
    }, context_instance=RequestContext(request))
