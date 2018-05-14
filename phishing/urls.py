from django.conf.urls import url
from django.views.generic import RedirectView

from phishing.views import tracker
from .views import campaign, landing_page, target, email_template, attachment

urlpatterns = [
    url(r'^$',
        RedirectView.as_view(pattern_name='campaign_list', permanent=False)),

    # campaigns
    url(r'^campaigns/$', campaign.ListCampaign.as_view(),
        name='campaign_list'),
    url(r'^campaigns/add$', campaign.CreateCampaign.as_view(),
        name='campaign_add'),
    url(r'^campaigns/delete/(?P<pk>\d+)/$', campaign.Delete.as_view(),
        name='campaign_delete'),
    url(r'^campaigns/dashboard/(?P<pk>\d+)/$', campaign.dashboard,
        name='campaign_dashboard'),

    # attachments
    url(r'^attachments/$', attachment.ListAttachment.as_view(),
        name='attachment_list'),
    url(r'^attachments/add$', attachment.CreateAttachment.as_view(),
        name='attachment_add'),
    url(r'^attachments/edit/(?P<pk>\d+)/$',
        attachment.UpdateAttachment.as_view(), name='attachment_edit'),
    url(r'^attachments/delete/(?P<pk>\d+)/$',
        attachment.DeleteAttachment.as_view(), name='attachment_delete'),

    # landing page
    url(r'^landing-page/$', landing_page.List.as_view(),
        name='landing_page_list'),
    url(r'^landing-page/add$', landing_page.Create.as_view(),
        name='landing_page_add'),
    url(r'^landing-page/clone-url$', landing_page.clone,
        name='landing_page_clone_url'),
    url(r'^landing-page/delete/(?P<pk>\w+)$', landing_page.Delete.as_view(),
        name='landing_page_delete'),
    url(r'^landing-page/post/(?P<tracker_id>[0-9a-z-]+)$',
        landing_page.landing_page_post, name='landing_page_post'),
    url(r'^landing-page/update/(?P<pk>\w+)$', landing_page.Edit.as_view(),
        name='landing_page_edit'),
    url(r'^lp/view/(?P<tracker_id>[0-9a-z-]+)$',
        landing_page.landing_page, name='landing_page'),

    # email template
    url(r'^email-template/$', email_template.ListEmailTemplate.as_view(),
        name='email_template_list'),
    url(r'^email-template/add$', email_template.CreateEmailTemplate.as_view(),
        name='email_template_add'),
    url(r'^email-template/edit/(?P<pk>\d+)/$',
        email_template.EditEmailTemplate.as_view(),
        name='email_template_edit'),
    url(r'^email-template/delete/(?P<pk>\d+)/$',
        email_template.Delete.as_view(), name='email_template_delete'),
    url(r'^email-template/clone/(?P<pk>\d+)/$',
        email_template.clone_email_template, name='email_template_clone'),

    # target group
    url(r'^targets-group/$', target.ListTargetGroup.as_view(),
        name='target_group_list'),
    url(r'^targets-group/add$', target.CreateTargetGroup.as_view(),
        name='target_group_add'),
    url(r'^targets-group/edit/(?P<pk>\d+)/$', target.EditTargetGroup.as_view(),
        name='target_group_edit'),
    url(r'^targets-group/delete/(?P<pk>\d+)/$', target.Delete.as_view(),
        name='target_group_delete'),

    # tracker
    url(r'^tracker/(?P<tracker_id>[0-9a-z-]+)$', tracker.set_info,
        name='tracker_set_infos'),
    url(r'^tracker/(?P<tracker_id>[0-9a-z-]+).png', tracker.img,
        name='tracker_img'),
]
