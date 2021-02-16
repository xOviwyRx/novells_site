from django.shortcuts import render
from django.views.generic import DetailView

from .models import Novell, Chapter
from django.http import HttpResponse


# Create your views here.
def index(request):
    pop_novell = Novell.objects.order_by('-views').first()
    shedule_chapter = Chapter.objects.filter(status=False).order_by('publish')[:4]
    all_novells = Novell.objects.all()
    return render(request, 'core/test.html', {'pop': pop_novell,
                                              'shedule_chapter': shedule_chapter,
                                              'all_novells': all_novells,
                                              })



class NovellDetailView(DetailView):
    model = Novell
    context_object_name = 'novell'
    template_name = 'core/novell_profile.html'