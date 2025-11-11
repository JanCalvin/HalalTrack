from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [

        path('',views.awal, name='awal'),
        path('pendaftaran_mitra',views.pendaftaran_mitra, name='pendaftaran_mitra'),
        path('login',views.loginview, name='login'),
        path('dashboard',views.dashboard, name='dashboard'),
      
        path('performlogin',views.performlogin,name="performlogin"),
        path('performlogout',views.performlogout,name="performlogout"),

        path('read_manufaktur',views.read_manufaktur, name='read_manufaktur'),
        path('create_manufaktur',views.create_manufaktur, name='create_manufaktur'),
        path('update_manufaktur/<str:id>',views.update_manufaktur, name='update_manufaktur'),
        path('delete_manufaktur/<str:id>',views.delete_manufaktur, name='delete_manufaktur'),
    
        path('update_status/<str:id>/<str:value>',views.update_status, name='update_status'),
        path('update_status2/<str:id>',views.update_status2, name='update_status2'),
        path('update_status3/<str:id>/<str:value>',views.update_status3, name='update_status3'),

       
        path('read_auditor',views.read_auditor, name='read_auditor'),
        path('create_auditor',views.create_auditor, name='create_auditor'),
        path('update_auditor/<str:id>',views.update_auditor, name='update_auditor'),
        path('delete_auditor/<str:id>',views.delete_auditor, name='delete_auditor'),
    
        path('read_admin',views.read_admin, name='read_admin'),
        path('create_admin',views.create_admin, name='create_admin'),
        path('update_admin/<str:id>',views.update_admin, name='update_admin'),
        path('delete_admin/<str:id>',views.delete_admin, name='delete_admin'),
    
        path('read_bahanbaku',views.read_bahanbaku, name='read_bahanbaku'),
        path('create_bahanbaku',views.create_bahanbaku, name='create_bahanbaku'),
        path('update_bahanbaku/<str:id>',views.update_bahanbaku, name='update_bahanbaku'),
        path('delete_bahanbaku/<str:id>',views.delete_bahanbaku, name='delete_bahanbaku'),

        path('read_produk',views.read_produk, name='read_produk'),
        path('create_produk',views.create_produk, name='create_produk'),
        path('update_produk/<str:id>',views.update_produk, name='update_produk'),
        path('delete_produk/<str:id>',views.delete_produk, name='delete_produk'),
        
        path('read_detail',views.read_detail, name='read_detail'),
        path('create_detail',views.create_detail, name='create_detail'),
        path('update_detail/<str:id>',views.update_detail, name='update_detail'),
        path('delete_detail/<str:id>',views.delete_detail, name='delete_detail'),
        
        path('hasil_halal',views.hasil_halal, name='hasil_halal'),
        path("diagram/<str:id>", views.diagram, name="diagram")
]
