from django.contrib import admin
from . import models
# Register your models here.

admin.site.register(models.Manufaktur)
admin.site.register(models.Produk)
admin.site.register(models.Supplier)
admin.site.register(models.ProdukSupplier)
admin.site.register(models.DetailProdukSupplier)
admin.site.register(models.LPHAdmin)
admin.site.register(models.LPHAuditor)
admin.site.register(models.LogSistem)
admin.site.register(models.KeputusanSistem)
