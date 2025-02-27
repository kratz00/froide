from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

from froide.account.forms import NewUserForm, AddressForm
from froide.team.views import AssignTeamView
from froide.helper.utils import render_400, render_403, get_redirect

from ..models import FoiRequest, FoiEvent
from ..forms import (
    ConcreteLawForm, TagFoiRequestForm, FoiRequestStatusForm,
    MakePublicBodySuggestionForm, PublicBodySuggestionsForm,
    ExtendDeadlineForm
)
from ..utils import check_throttle
from ..services import (
    CreateSameAsRequestService, ActivatePendingRequestService
)
from ..auth import can_write_foirequest
from ..hooks import registry

from .request import show_foirequest
from .make_request import get_new_account_url


def allow_write_foirequest(func):
    def inner(request, slug, *args, **kwargs):
        foirequest = get_object_or_404(FoiRequest, slug=slug)
        if not can_write_foirequest(foirequest, request):
            return render_403(request)
        return func(request, foirequest, *args, **kwargs)
    return inner


@require_POST
@allow_write_foirequest
def set_public_body(request, foirequest):
    form = PublicBodySuggestionsForm(request.POST, foirequest=foirequest)
    if not form.is_valid():
        return render_400(request)

    throttle_message = check_throttle(request.user, FoiRequest)
    if throttle_message:
        messages.add_message(request, messages.ERROR, '\n'.join(throttle_message))
        return render_400(request)

    form.save()

    messages.add_message(
        request,
        messages.SUCCESS,
        _('Request was sent to: {name}.').format(
            name=foirequest.public_body.name)
    )
    return redirect(foirequest)


@require_POST
def suggest_public_body(request, slug):
    foirequest = get_object_or_404(FoiRequest, slug=slug)
    if not foirequest.needs_public_body():
        return render_400(request)
    form = MakePublicBodySuggestionForm(request.POST)
    if form.is_valid():
        publicbody = form.publicbody_object
        user = None
        if request.user.is_authenticated:
            user = request.user
        response = foirequest.suggest_public_body(
            publicbody,
            form.cleaned_data['reason'],
            user
        )
        if response:
            messages.add_message(request, messages.SUCCESS,
                _('Your Public Body suggestion has been added.'))
        else:
            messages.add_message(request, messages.WARNING,
                _('This Public Body has already been suggested.'))
        return redirect(foirequest)

    messages.add_message(request, messages.ERROR,
            _("You need to specify a Public Body!"))
    return render_400(request)


@require_POST
@allow_write_foirequest
def set_status(request, foirequest):
    form = FoiRequestStatusForm(request.POST, foirequest=foirequest)
    if form.is_valid():
        form.set_status()
        messages.add_message(request, messages.SUCCESS,
                _('Status of request has been updated.'))
        response = registry.run_hook(
            'post_status_set',
            request,
            user=request.user,
            data={'foirequest': foirequest, 'form': form}
        )
        if response is not None:
            return response
    else:
        messages.add_message(request, messages.ERROR,
        _('Invalid value for form submission!'))
        return show_foirequest(request, foirequest, context={
            "status_form": form
        }, status=400)
    return redirect(foirequest.get_absolute_url() + '#-')


@require_POST
@allow_write_foirequest
def make_public(request, foirequest):
    if not foirequest.is_foi:
        return render_400(request)
    foirequest.make_public()
    return redirect(foirequest)


@require_POST
@allow_write_foirequest
def set_law(request, foirequest):
    if not foirequest.response_messages():
        return render_400(request)
    if not foirequest.law.meta:
        return render_400(request)
    form = ConcreteLawForm(request.POST, foirequest=foirequest)
    if not form.is_valid():
        return render_400(request)
    form.save()
    messages.add_message(request, messages.SUCCESS,
            _('A concrete law has been set for this request.'))
    return redirect(foirequest)


@require_POST
@allow_write_foirequest
def set_tags(request, foirequest):
    form = TagFoiRequestForm(request.POST)
    if form.is_valid():
        form.save(foirequest)
        messages.add_message(request, messages.SUCCESS,
                _('Tags have been set for this request'))
    return redirect(foirequest)


@require_POST
@allow_write_foirequest
def set_summary(request, foirequest):
    if not foirequest.status_is_final():
        return render_400(request)
    summary = request.POST.get('summary', None)
    if summary is None:
        return render_400(request)
    foirequest.summary = summary
    foirequest.save()
    messages.add_message(request, messages.SUCCESS,
                _('The outcome summary has been saved.'))
    return redirect(foirequest)


@require_POST
def mark_not_foi(request, slug):
    foirequest = get_object_or_404(FoiRequest, slug=slug)
    if not request.user.is_authenticated:
        return render_403(request)
    if not request.user.is_staff:
        return render_403(request)
    foirequest.is_foi = False
    foirequest.public = False
    foirequest.visibility = FoiRequest.VISIBLE_TO_REQUESTER
    foirequest.save()
    if request.is_ajax():
        return HttpResponse()
    messages.add_message(request, messages.SUCCESS,
            _('Request marked as not a FoI request.'))
    return redirect(foirequest)


@require_POST
def mark_checked(request, slug):
    foirequest = get_object_or_404(FoiRequest, slug=slug)
    if not request.user.is_authenticated:
        return render_403(request)
    if not request.user.is_staff:
        return render_403(request)
    foirequest.checked = True
    foirequest.save()
    if request.is_ajax():
        return HttpResponse()
    messages.add_message(request, messages.SUCCESS,
            _('Request marked as checked.'))
    return redirect(foirequest)


@require_POST
def make_same_request(request, slug):
    foirequest = get_object_or_404(FoiRequest, slug=slug)
    if not foirequest.not_publishable:
        return redirect(foirequest)
    if foirequest.same_as is not None:
        foirequest = foirequest.same_as

    if not request.user.is_authenticated:
        new_user_form = NewUserForm(request.POST)
        if not new_user_form.is_valid():
            return show_foirequest(request, foirequest,
                context={"new_user_form": new_user_form}, status=400)
    else:
        user = request.user
        if foirequest.user == user:
            return render_400(request)
        same_requests = FoiRequest.objects.filter(user=user, same_as=foirequest).exists()
        if same_requests:
            messages.add_message(request, messages.ERROR,
                _("You already made an identical request"))
            return render_400(request)
        address_form = AddressForm(request.POST)
        if address_form.is_valid():
            address_form.save(user)

    throttle_message = check_throttle(request.user, FoiRequest)
    if throttle_message:
        messages.add_message(request, messages.ERROR, '\n'.join(throttle_message))
        return render_400(request)

    body = foirequest.description
    if foirequest.status_is_final():
        body = "{}\n\n{}" .format(
            foirequest.description,
            _('Please see this request on %(site_name)s where you granted access to this information: %(url)s') % {
                'url': foirequest.get_absolute_domain_short_url(),
                'site_name': settings.SITE_NAME
            }
        )

    data = {
        'user': request.user,
        'publicbodies': [foirequest.public_body],
        'subject': foirequest.title,
        'body': body,
        'public': foirequest.public,
        'original_foirequest': foirequest
    }
    if request.POST.get('redirect_url'):
        data['redirect_url'] = request.POST['redirect_url']
    if request.POST.get('reference'):
        data['reference'] = request.POST['reference']

    if not request.user.is_authenticated:
        data.update(new_user_form.cleaned_data)

    service = CreateSameAsRequestService(data)
    new_foirequest = service.execute(request)

    count = FoiRequest.objects.filter(same_as=foirequest).count()
    FoiRequest.objects.filter(id=foirequest.id).update(same_as_count=count)

    if request.user.is_active:
        messages.add_message(request, messages.SUCCESS,
                _('You successfully requested this document! '
                  'Your request is displayed below.'))
        return redirect(new_foirequest)
    else:
        messages.add_message(request, messages.INFO,
                _('Please check your inbox for mail from us to '
                  'confirm your mail address.'))
        # user cannot access the request yet!
        return redirect(get_new_account_url(new_foirequest))


@require_POST
@allow_write_foirequest
def extend_deadline(request, foirequest):
    form = ExtendDeadlineForm(request.POST)
    if form.is_valid():
        form.save(foirequest)
        messages.add_message(request, messages.INFO,
                _('Deadline has been extended.'))
        FoiEvent.objects.create_event('deadline_extended', foirequest)
        return redirect(foirequest)
    return render_400(request)


class SetTeamView(AssignTeamView):
    model = FoiRequest


@require_POST
@allow_write_foirequest
def confirm_request(request, foirequest):
    if foirequest.status != 'awaiting_user_confirmation':
        return render_400(request)

    req_service = ActivatePendingRequestService({'foirequest': foirequest})
    foirequest = req_service.process(request=request)
    if not foirequest:
        return render_400(request)

    return redirect(foirequest)


@require_POST
@allow_write_foirequest
def delete_request(request, foirequest):
    if foirequest.status != 'awaiting_user_confirmation':
        return render_400(request)

    if foirequest.user != request.user:
        return render_400(request)

    foirequest.delete()

    return get_redirect(request)
