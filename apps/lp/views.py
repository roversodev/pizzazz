import locale
from django.shortcuts import render


locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
# Create your views here.
def lp(request):
    return render(request, 'lp/lp.html')

def lp_empresa(request):
    return render(request, 'lp/lp-empresa.html')