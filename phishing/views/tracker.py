import json
import os

from django.http import HttpResponse, HttpResponseNotFound
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt


from phishing.models import Tracker, TrackerInfos


def img(request, tracker_id):
    """Send tracking image.

    :param request:
    :param tracker_id:
    :return:
    """
    tracker = get_object_or_404(Tracker, pk=tracker_id)

    # has data ?
    data = request.GET.dict().copy()
    data.update(request.POST.dict().copy())
    raw = json.dumps(data) if data else None

    # add infos
    TrackerInfos.create(target_tracker=tracker, http_request=request, raw=raw)
    count = TrackerInfos.objects.filter(target_tracker=tracker).count()

    # update values
    tracker.value = 'opened'
    tracker.infos = count
    tracker.save()

    # return image
    app_path = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(app_path, '../static/img/tracking.png')
    with open(image_path, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')


@csrf_exempt
def set_info(request, tracker_id):
    """Set browser infos.

    :param request:
    :param tracker_id:
    :return:
    """
    if not request.POST.get('infos'):
        return HttpResponseBadRequest()

    tracker = TrackerInfos.objects.filter(
        target_tracker_id=tracker_id, raw=None).order_by('created_at').last()

    if not tracker:
        return HttpResponseNotFound()

    tracker.raw = request.POST['infos']
    tracker.save()

    return HttpResponse('')
