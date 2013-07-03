from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from . import models


class EventList(ListView):
    paginate_by = 20

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(EventList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return models.Event.objects.order_by('-datetime', '-id')
