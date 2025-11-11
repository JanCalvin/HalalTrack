from django.db import models
import random
import uuid
import string
# from django.utils import timezone
# Create your models here.

def generate_id() :
    letters = ''.join(random.choices(string.ascii_uppercase,k=2))
    numbers = ''.join(random.choices(string.digits,k=6))
    return letters+numbers

class LPHAdmin(models.Model) :
    id_lph_admin = models.AutoField(primary_key=True)
    nama_admin = models.CharField(max_length=100)
    email = models.EmailField()
    kantor = models.TextField()
    username = models.CharField(max_length=100)
    tanggal_dibuat =  models.DateTimeField(auto_now_add=True)
    
    def __str__ (self) : 
        return f'{self.nama_admin}'
    
class LPHAuditor(models.Model) :
    id_lph_auditor = models.AutoField(primary_key=True)
    id_lph_admin = models.ForeignKey(LPHAdmin,on_delete=models.CASCADE)
    nama_auditor = models.CharField(max_length=100)
    jabatan = models.CharField(max_length=100)
    email = models.EmailField()
    nomor_telepon = models.PositiveBigIntegerField()
    username = models.CharField(max_length=100)
    tanggal_dibuat =  models.DateTimeField(auto_now_add=True)
    
    def __str__ (self) : 
        return f'{self.nama_auditor}'
    

class Manufaktur(models.Model) :
    id_manufaktur = models.AutoField(primary_key=True)
    '''ASSIGN BY ADMIN'''
    id_lph_auditor = models.ForeignKey(LPHAuditor,on_delete=models.CASCADE,null=True,blank=True)
    '''ACC'''
    id_lph_admin = models.ForeignKey(LPHAdmin,on_delete=models.CASCADE,null=True,blank=True)
    nama_usaha = models.CharField(max_length=300)
    alamat = models.TextField()
    jenis_produk = models.CharField(max_length=100)
    contact = models.PositiveBigIntegerField()
    email = models.EmailField(null=True,blank=True)
    username = models.CharField(max_length=100,null=True,blank=True)
    status_akun = models.BooleanField(default=False)
    tanggal_dibuat = models.DateTimeField(auto_now_add=True)
    catatan_regis = models.TextField(blank=True,null=True)
    ktp = models.URLField(blank=True, null=True)
    nib = models.URLField(blank=True, null=True)
    def __str__ (self) : 
      
        return f'{self.nama_usaha}'
    
class Produk(models.Model) :
    id_produk = models.CharField(primary_key=True,max_length=10,unique=True,editable=False,default=generate_id)
    id_manufaktur = models.ForeignKey(Manufaktur,on_delete=models.CASCADE)
    nama_produk = models.CharField(max_length=100)
    status_halal = models.CharField(max_length=100, default='Belum Halal')
    qr_code = models.URLField(blank=True, null=True)
    tanggal_generate = models.DateTimeField(auto_now_add=True)
    catatan = models.TextField(blank=True,null=True)
    def __str__ (self) : 
        return f'{self.nama_produk}-{self.id_manufaktur}'
    
# class Supplier(models.Model) :
#     id_supplier = models.AutoField(primary_key=True)
#     id_manufaktur = models.ForeignKey(Manufaktur,on_delete=models.CASCADE)
#     nama_supplier = models.CharField(max_length=100)
#     jenis_bahanbaku = models.CharField(max_length=100)
#     asal_bahan = models.CharField(max_length=100)
#     status_halal = models.CharField(max_length=100, default='Belum Halal')
#     def __str__ (self) : 
       
#         return f'{self.pembuat_data}-{self.nama_supplier}-{self.status_halal}'
    
    
class BahanBaku(models.Model) :
    id_bahanbaku = models.AutoField(primary_key=True)
    id_manufaktur = models.ForeignKey(Manufaktur,on_delete=models.CASCADE)
    nama_bahanbaku = models.CharField(max_length=100)
    nama_supplier = models.CharField(max_length=100)
    status_halal = models.CharField(max_length=100, default='Belum Halal')
    def __str__ (self) : 
       
        return f'{self.id_manufaktur}-{self.nama_bahanbaku}-{self.status_halal}'


class ProdukSupplier(models.Model) :
    id_produk_supplier = models.AutoField(primary_key=True)
    id_produk = models.ForeignKey(Produk,on_delete=models.CASCADE)
    catatan_auditor= models.TextField(blank=True, null=True)
    verifikasi_auditor = models.BooleanField(default=False)
    def __str__ (self) : 
        return f'{self.id_produk_supplier}'
    
    
class DetailProdukSupplier(models.Model) :
    id_detail_produk_supplier = models.AutoField(primary_key=True)
    id_produk_supplier = models.ForeignKey(ProdukSupplier,on_delete=models.CASCADE)
    id_bahanbaku = models.ForeignKey(BahanBaku,on_delete=models.CASCADE)
    

    def __str__ (self) : 
        return f'{self.id_detail_produk_supplier}'



