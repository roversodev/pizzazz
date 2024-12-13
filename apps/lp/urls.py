from django.urls import path, re_path
from apps.lp import views

urlpatterns = [

    # The home page
    path('', views.lp, name='lp_app'),
    path('lp-empresa', views.lp_empresa, name='lp_empresa'),

]
