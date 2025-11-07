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
    id_lph_auditor = models.ForeignKey(LPHAuditor,on_delete=models.CASCADE,null=True,blank=True)
    id_lph_admin = models.ForeignKey(LPHAdmin,on_delete=models.CASCADE,null=True,blank=True)
    nama_usaha = models.CharField(max_length=300)
    alamat = models.TextField()
    jenis_produk = models.CharField(max_length=100)
    status_halal = models.CharField(max_length=100, default='Belum Halal')
    contact = models.PositiveBigIntegerField()
    email = models.EmailField()
    username = models.CharField(max_length=100)
    status_akun = models.BooleanField(default=False)
    tanggal_dibuat = models.DateTimeField(auto_now_add=True)
    catatan_regis = models.TextField(blank=True,null=True)
    def __str__ (self) : 
      
        return f'{self.nama_usaha}-{self.status_halal}'
    
class Produk(models.Model) :
    id_produk = models.CharField(primary_key=True,max_length=10,unique=True,editable=False,default=generate_id)
    id_manufaktur = models.ForeignKey(Manufaktur,on_delete=models.CASCADE)
    nama_produk = models.CharField(max_length=100)
    status_analisis = models.CharField(max_length=100)
    qr_code = models.URLField(blank=True, null=True)
    tanggal_generate = models.DateTimeField(auto_now_add=True)
    catatan = models.TextField(blank=True,null=True)
    def __str__ (self) : 
        return f'{self.nama_produk}-{self.id_manufaktur}'
    
class Supplier(models.Model) :
    id_supplier = models.AutoField(primary_key=True)
    id_manufaktur = models.ForeignKey(Manufaktur,on_delete=models.CASCADE)
    nama_supplier = models.CharField(max_length=100)
    jenis_bahanbaku = models.CharField(max_length=100)
    asal_bahan = models.CharField(max_length=100)
    status_halal = models.CharField(max_length=100, default='Belum Halal')
    def __str__ (self) : 
       
        return f'{self.pembuat_data}-{self.nama_supplier}-{self.status_halal}'
    
class ProdukSupplier(models.Model) :
    id_produk_supplier = models.AutoField(primary_key=True)
    id_produk = models.ForeignKey(Produk,on_delete=models.CASCADE)

    def __str__ (self) : 
        return f'{self.id_produk_supplier}'
    
class DetailProdukSupplier(models.Model) :
    id_detail_produk_supplier = models.AutoField(primary_key=True)
    id_produk_supplier = models.ForeignKey(ProdukSupplier,on_delete=models.CASCADE)
    id_supplier = models.ForeignKey(Supplier,on_delete=models.CASCADE)
    peran_supplier = models.CharField(max_length=100)
    catatan_rantai_pasok = models.TextField()

    def __str__ (self) : 
        return f'{self.id_detail_produk_supplier}'

class LogSistem(models.Model) :
    id_log =  models.AutoField(primary_key=True)
    logis_as = models.CharField(max_length=100)
    jenis_aktivitas = models.CharField(max_length=100)
    waktu_akses  = models.DateTimeField(auto_now_add=True)
    status_respon = models.CharField(max_length=100)
    ip_address = models.CharField(max_length=200)
    
    def __str__ (self) : 
        return f'{self.id_log}'


class KeputusanSistem(models.Model) :
    id_keputusan =  models.AutoField(primary_key=True)
    id_lph_auditor = models.ForeignKey(LPHAuditor,on_delete=models.CASCADE)
    id_produk = models.ForeignKey(Produk,on_delete=models.CASCADE)
    nilai_m = models.BooleanField(default=False)
    nilai_s = models.BooleanField(default=False)
    kombinasi_parameter  = models.TextField()
    keputusan_sistem  = models.TextField()
    deskripsi_keputusan_sistem  = models.TextField()
    rekomendasi_perbaikan  = models.TextField()
    tanggal_analisis  = models.DateTimeField(auto_now_add=True)
    
    def __str__ (self) : 
        return f'{self.id_keputusan} - {self.tanggal_analisis}'
    

