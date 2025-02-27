from django.conf.urls import url
from django.utils.translation import pgettext_lazy

from ..feeds import FoiRequestFeed, FoiRequestFeedAtom
from ..views import (
    shortlink, auth, show, suggest_public_body, set_public_body,
    set_status, send_message, escalation_message, make_public,
    confirm_request, delete_request,
    set_law, set_tags, set_summary, add_postal_reply,
    add_postal_message, add_postal_reply_attachment,
    set_message_sender, mark_not_foi, mark_checked,
    extend_deadline, approve_attachment, approve_message,
    make_same_request, resend_message,
    download_foirequest_zip, download_foirequest_pdf,
    show_attachment, redact_attachment,
    upload_attachments, delete_attachment, create_document,
    SetTeamView, edit_message, redact_message
)

urlpatterns = [
    url(r"^(?P<obj_id>\d+)$", shortlink, name="foirequest-notsolonglink"),
    url(r"^(?P<obj_id>\d+)/auth/(?P<code>[0-9a-f]+)/$", auth, name="foirequest-longerauth"),
    url(r"^(?P<slug>[-\w]+)/$", show, name="foirequest-show"),
    url(r"^(?P<slug>[-\w]+)/suggest/public-body/$", suggest_public_body, name="foirequest-suggest_public_body"),
    url(r"^(?P<slug>[-\w]+)/set/public-body/$", set_public_body, name="foirequest-set_public_body"),
    url(r"^(?P<slug>[-\w]+)/set/status/$", set_status, name="foirequest-set_status"),
    url(r"^(?P<slug>[-\w]+)/send/message/$", send_message, name="foirequest-send_message"),
    url(r"^(?P<slug>[-\w]+)/escalation/message/$", escalation_message, name="foirequest-escalation_message"),
    url(r"^(?P<slug>[-\w]+)/make/public/$", make_public, name="foirequest-make_public"),
    url(r"^(?P<slug>[-\w]+)/confirm-request/$", confirm_request, name="foirequest-confirm_request"),
    url(r"^(?P<slug>[-\w]+)/delete-request/$", delete_request, name="foirequest-delete_request"),
    url(r"^(?P<slug>[-\w]+)/set/law/$", set_law, name="foirequest-set_law"),
    url(r"^(?P<slug>[-\w]+)/set/tags/$", set_tags, name="foirequest-set_tags"),
    url(r"^(?P<slug>[-\w]+)/set/resolution/$", set_summary, name="foirequest-set_summary"),
    url(r"^(?P<slug>[-\w]+)/add/postal-reply/$", add_postal_reply, name="foirequest-add_postal_reply"),
    url(r"^(?P<slug>[-\w]+)/add/postal-message/$", add_postal_message, name="foirequest-add_postal_message"),
    url(r"^(?P<slug>[-\w]+)/mark/not-foi/$", mark_not_foi, name="foirequest-mark_not_foi"),
    url(r"^(?P<slug>[-\w]+)/mark/checked/$", mark_checked, name="foirequest-mark_checked"),
    url(r"^(?P<slug>[-\w]+)/extend-deadline/$", extend_deadline, name="foirequest-extend_deadline"),
    url(r"^(?P<slug>[-\w]+)/make-same/$", make_same_request, name="foirequest-make_same_request"),
    url(r"^(?P<slug>[-\w]+)/resend/$", resend_message, name="foirequest-resend_message"),
    url(r"^(?P<slug>[-\w]+)/download/$", download_foirequest_zip, name="foirequest-download"),
    url(r"^(?P<slug>[-\w]+)/pdf/$", download_foirequest_pdf, name="foirequest-pdf"),
    url(r"^(?P<slug>[-\w]+)/set-team/$", SetTeamView.as_view(), name="foirequest-set_team"),
    # Messages
    url(r"^(?P<slug>[-\w]+)/add/postal-reply/(?P<message_id>\d+)/$", add_postal_reply_attachment, name="foirequest-add_postal_reply_attachment"),
    url(r"^(?P<slug>[-\w]+)/approve/message/(?P<message_id>\d+)/$", approve_message, name="foirequest-approve_message"),
    url(r"^(?P<slug>[-\w]+)/(?P<message_id>\d+)/set-public-body/$", set_message_sender, name="foirequest-set_message_sender"),
    url(r"^(?P<slug>[-\w]+)/(?P<message_id>\d+)/edit-message/$", edit_message, name="foirequest-edit_message"),
    url(r"^(?P<slug>[-\w]+)/(?P<message_id>\d+)/redact-message/$", redact_message, name="foirequest-redact_message"),
    # Attachments
    url(pgettext_lazy('url part', r'^(?P<slug>[-\w]+)/(?P<message_id>\d+)/attachment/(?P<attachment_name>.+)$'),
        show_attachment, name='foirequest-show_attachment'),
    # Attachment Upload
    url(pgettext_lazy('url part', r'^(?P<slug>[-\w]+)/(?P<message_id>\d+)/upload/$'),
        upload_attachments, name='foirequest-upload_attachments'),

    # Attachment actions
    url(r"^(?P<slug>[-\w]+)/redact/(?P<attachment_id>\d+)/$", redact_attachment, name="foirequest-redact_attachment"),
    url(r"^(?P<slug>[-\w]+)/approve/(?P<attachment>\d+)/$", approve_attachment, name="foirequest-approve_attachment"),
    url(r"^(?P<slug>[-\w]+)/delete/(?P<attachment>\d+)/$", delete_attachment, name="foirequest-delete_attachment"),
    url(r"^(?P<slug>[-\w]+)/create-doc/(?P<attachment>\d+)/$", create_document, name="foirequest-create_document"),

    # Feed
    url(r"^(?P<slug>[-\w]+)/feed/$", FoiRequestFeedAtom(), name="foirequest-feed_atom"),
    url(r"^(?P<slug>[-\w]+)/rss/$", FoiRequestFeed(), name="foirequest-feed")
]
