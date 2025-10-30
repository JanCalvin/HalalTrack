from django.shortcuts import render
from django.shortcuts import render, redirect
from . import models
from datetime import datetime
import calendar
from .decorators import role_required
from django.http import HttpResponse,JsonResponse
from django.contrib import messages
from django.contrib.auth import login , logout, authenticate
from django.contrib.auth.decorators import login_required
# from .decorators import role_required
from django.forms import DateInput
from django.db.models import F,Q,Sum,Value,Count
import math
from django.template.loader import render_to_string
import tempfile
from django.urls import reverse 
# from weasyprint import HTML
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import openpyxl
from django.db import transaction
from openpyxl.styles import Font, Alignment,PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.styles import Border, Side
from django.db import connection
from types import SimpleNamespace
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from utils.supabase_upload import upload_file_and_get_url, delete_file_by_public_url
from utils.supabase_upload import upload_bytes_and_get_url   # <-- pakai BYTES
from utils.qr_code import make_qr_png_bytes
from django.contrib.auth.models import User, Group
# views.py
import re
from django.contrib.auth import update_session_auth_hash  # kalau ubah pw user yang sedang login
def loginview(request):
    if request.user.is_authenticated:
        group = None
        if request.user.groups.exists():
            group = request.user.groups.all()[0].name

        if group == 'manufaktur':
            return redirect('read_produk')
        elif group == 'admin' :
            return redirect('read_auditor')
        else:
            return redirect('read_manufaktur') 
    else:
        return render(request, "base/login.html")

def performlogin(request):
    if request.method != "POST":
        return HttpResponse("Method not Allowed")
    else:
        username_login = request.POST['username']
        password_login = request.POST['password']
        userobj = authenticate(request, username=username_login, password=password_login)
        request.session['username']  = username_login 
        print('cek aja bang',request.session)
        if userobj is not None:
            login(request, userobj)
            messages.success(request, "Login sukses")
            if userobj.groups.filter(name='manufaktur').exists():
                return redirect("read_produk")
            elif userobj.groups.filter(name='admin').exists() :
                return redirect('read_auditor')
            return redirect('read_manufaktur') 
          
        else:
            messages.error(request, "Username atau Password salah !!!")
            return redirect("login")


@login_required(login_url="login")
def logoutview(request):
    logout(request)
    messages.info(request,"Berhasil Logout")
    return redirect('login')

@login_required(login_url="login")
def performlogout(request):
    logout(request)
    return redirect("login")
# Create your views here.
ID_RE = re.compile(r'[A-Z]{2}\d{6}')

def awal(request):
    if request.method != 'POST':
        return render(request, 'base/awalan.html')

    # Teks pencarian dari input atau hasil decode jsQR
    q_raw = (request.POST.get('q') or '').strip()

    # Jika QR payload berisi ID di tengah2 teks, ambil ID-nya;
    # kalau tidak ada match, pakai apa adanya untuk fuzzy search.
    m = ID_RE.search(q_raw.upper())
    q = m.group(0) if m else q_raw

    getproduk = None
    if q:
      getproduk = (
          models.Produk.objects
          .select_related('id_manufaktur')
          .filter(
              Q(id_produk__iexact=q) |
              Q(nama_produk__icontains=q) |
              Q(id_manufaktur__nama_usaha__icontains=q)
          )
          .first()
      )

    if not getproduk:
        messages.error(
            request,
            'Produk tidak ditemukan.' if q else 'QR tidak terbaca atau kosong.'
        )

    return render(request, 'base/awalan.html', {
        'getproduk': getproduk,
        'nama_produk': q_raw,   # tampilkan apa yg diketik/terbaca
    })
    
# def awal(request):
#     # Hanya me-return halaman statis, tanpa mengakses database atau logic kompleks
#     return render(request, 'base/awalan.html')

'''CRUD manufaktur'''
@login_required(login_url="login")
@role_required(['admin','auditor','manufaktur'])
def read_manufaktur(request) :
    filtermanufaktur = request.GET.get('filtermanufaktur','')
    print('filtermanufaktur',filtermanufaktur)
    user = request.user
    is_admin = user.groups.filter(name__iexact='admin').exists()
    if filtermanufaktur == '' or filtermanufaktur == 'All' :
        manufakturobj = models.Manufaktur.objects.all()
        print('halo',manufakturobj)
    elif filtermanufaktur == 'True' :
        manufakturobj = models.Manufaktur.objects.filter(status_akun=True)
    else :
        manufakturobj = models.Manufaktur.objects.filter(status_akun=False)
    if not manufakturobj.exists():
        messages.error(request, "Data manufaktur Tidak Ditemukan!")
    return render(request, 'manufaktur/read_manufaktur.html', {'manufakturobj': manufakturobj,'filtermanufaktur':filtermanufaktur,'is_admin' : is_admin})


@login_required(login_url="login")
@role_required(['admin','auditor'])
def create_manufaktur(request):
    # groupobj = Group.objects.all().order_by('name')
    user = request.user
    username = user.username
    is_admin = user.groups.filter(name__iexact='admin').exists()
    
    if request.method == "GET":
        return render(request, 
                      'manufaktur/create_manufaktur.html', {'is_admin' :is_admin})
    else :
      
        id_lph_auditor = request.POST.get("id_lph_auditor",'')
        id_lph_admin = request.POST.get("id_lph_admin",'')
        nama_usaha = request.POST["nama_usaha"]
        alamat = request.POST["alamat"]
        jenis_produk = request.POST["jenis_produk"]
        status_halal = request.POST["status_halal"]
        if status_halal == 'True' :
            status_halal = True
        else :
            status_halal = False
        contact = request.POST["contact"]
        # tanggal_dibuat = request.POST["tanggal_dibuat"]
        catatan_regis = request.POST["catatan_regis"]
        username   = (request.POST.get("username") or "").strip()
        email      = (request.POST.get("email") or "").strip()
        group_val  = 'manufaktur'
        password   = request.POST.get("password") or ""
        manufakturobj = models.Manufaktur.objects.filter(nama_usaha=nama_usaha,username=username)
        if not username or not password:
            messages.error(request, "Username dan password wajib diisi.")
            return render(request, "manufaktur/create_manufaktur.html", {
                "prefill": {"username": username, "email": email, "group": group_val}
            })

        if User.objects.filter(username=username,groups__name = group_val).exists():
            messages.error(request, "Username sudah ada!")
            return render(request, "manufaktur/create_manufaktur.html", {
                 "prefill": {"username": username, "email": email, "group": group_val}
            })
        if manufakturobj.exists():
            messages.error(request, "manufaktur sudah ada")
            return redirect("create_manufaktur")
        else:
            if is_admin :
                models.Manufaktur(
                    id_lph_admin=models.LPHAdmin.objects.get(username = id_lph_admin),
                    nama_usaha=nama_usaha,
                    alamat=alamat,
                    jenis_produk=jenis_produk,
                    status_halal=status_halal,
                    contact=contact,
                    email=email,
                    username=username,
    
                    catatan_regis=catatan_regis,
                    status_akun = True
                ).save()
            else :
                models.Manufaktur(
                    id_lph_auditor=models.LPHAuditor.objects.get(username = id_lph_auditor),
                    nama_usaha=nama_usaha,
                    alamat=alamat,
                    jenis_produk=jenis_produk,
                    status_halal=status_halal,
                    contact=contact,
                    email=email,
                    username=username,
                
                    catatan_regis=catatan_regis,
                    status_akun = True
                ).save()
                 # --- Resolve objek Group dari input (dukung ID atau nama) ---
            group = None
            if group_val:
                # Coba sebagai ID dulu
                try:
                    group = Group.objects.get(name=group_val)
                except (ValueError, Group.DoesNotExist):
                    # Bukan ID, coba sebagai nama
                    group, _ = Group.objects.get_or_create(name=group_val)
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username, password=password, email=email
                    )
                    if group:
                        user.groups.add(group)

                messages.success(request, "Akun berhasil dibuat. Silakan login. ")
            
            except Exception as e:
                messages.error(request, f"Gagal membuat akun: {e}")
                return render(request, "manufaktur/create_manufaktur.html", {
                    "prefill": {"username": username, "email": email, "group": group_val}
                })

            messages.success(request, "Data Manufaktur Berhasil Ditambahkan!")
        return redirect("read_manufaktur")
    
@login_required(login_url="login")  
@role_required(['auditor','admin'])
def update_status(request,id) :
    getmanufaktur = models.Manufaktur.objects.get(id_manufaktur = id)
    if getmanufaktur.status_halal == True :
        getmanufaktur.status_halal = False
    else :
        getmanufaktur.status_halal = False
    getmanufaktur.save()
    return redirect('read_manufaktur')
@login_required(login_url="login")
@role_required(['auditor','admin'])
def update_status2(request,id) :
    getmanufaktur = models.Manufaktur.objects.get(id_manufaktur = id)
    if getmanufaktur.status_akun == True :
        getmanufaktur.status_akun = False
    else :
        getmanufaktur.status_akun = False
    getmanufaktur.save()
    return redirect('read_manufaktur')

@login_required(login_url="login")
@role_required(['auditor','admin'])
def update_manufaktur(request, id):
    getmanufaktur = models.Manufaktur.objects.get(id_manufaktur=id)
    username1 =getmanufaktur.username
    getuser = User.objects.get(username=username1)
    if request.method == 'GET':
        status_halal = getmanufaktur.status_halal
        status_akun = getmanufaktur.status_akun
        tgl1 = getmanufaktur.tanggal_dibuat.strftime('%Y-%m-%d')
        return render(request, 'manufaktur/update_manufaktur.html', {
            'status_halal': status_halal,
            'status_akun': status_akun,
            'getmanufaktur': getmanufaktur,
            'getuser': getuser,
            'id': id,
            'tgl1': tgl1,
        })

    else:
        nama_usaha = request.POST["nama_usaha"]
        alamat = request.POST["alamat"]
        jenis_produk = request.POST["jenis_produk"]
        status_halal = request.POST["status_halal"]
        if status_halal == "True" :
            status_halal = True
        else :
            status_halal = False
        contact = request.POST["contact"]
        # tanggal_dibuat = request.POST["tanggal_dibuat"]
        catatan_regis = request.POST["catatan_regis"]
        username   = (request.POST.get("username") or "").strip()
        email      = (request.POST.get("email") or "").strip()
        password = (request.POST.get("email") or "").strip()
        if models.Manufaktur.objects.filter(nama_usaha=nama_usaha,username=username,contact=contact).exclude(id_manufaktur = id).exists() :
            messages.error(request,"Manufaktur sudah ada!")
            return render(request, 'manufaktur/update_manufaktur.html')

        getmanufaktur.nama_usaha = nama_usaha
        getmanufaktur.alamat = alamat
        getmanufaktur.jenis_produk = jenis_produk
        getmanufaktur.status_halal = status_halal
        # getmanufaktur.public_url = public_url
        getmanufaktur.email = email
        getmanufaktur.username = username
        # getmanufaktur.tanggal_dibuat = tanggal_dibuat
        getmanufaktur.catatan_regis = catatan_regis

        if User.objects.filter(username__iexact=username,groups__name__iexact = 'manufaktur').exclude(pk=getuser.id).exists() :
            messages.error(request, "Username sudah ada!")
            return render(request, "manufaktur/update_manufaktur.html", {
                 "prefill": {"username": username, "email": email, }
            })
        
        
        getuser.username = username
        getuser.email = email
        if password:                     # hanya kalau diisi
            getuser.set_password(password)   # <-- PENTING: hash password
        # kalau yang diubah adalah user yang sedang login sendiri:
            if request.user.pk == getuser.pk:
            # jaga sesi tetap valid setelah ganti password
                update_session_auth_hash(request, getuser)

        getuser.save()

        getmanufaktur.save()

        messages.success(request, "Data manufaktur berhasil diperbarui!")
        return redirect('read_manufaktur')
    
@login_required(login_url="login")
@role_required(['auditor','admin'])
def delete_manufaktur(request,id) :
    getmanufaktur = models.Manufaktur.objects.get(id_manufaktur=id)
    username = getmanufaktur.username
    User.objects.filter(username__iexact=username,groups__name__iexact = 'manufaktur').delete()
    getmanufaktur.delete()
    messages.success(request, "Data berhasil dihapus!")
    return redirect('read_manufaktur')


'''CRUD auditor'''
@login_required(login_url="login")
@role_required(['auditor','admin'])
def read_auditor(request) :
   
    user = request.user
    # is_admin = user.groups.filter(name__iexact='admin').exists()
    auditorobj = models.LPHAuditor.objects.all()
    if not auditorobj.exists():
        messages.error(request, "Data auditor Tidak Ditemukan!")
    return render(request, 'auditor/read_auditor.html', {'auditorobj': auditorobj})

@login_required(login_url="login")
@role_required(['admin'])
def create_auditor(request):
    # groupobj = Group.objects.all().order_by('name')
    # user = request.user
    # username = user.username
    # is_admin = user.groups.filter(name__iexact='admin').exists()
    if request.method == "GET":
        return render(request, 
                      'auditor/create_auditor.html',)
    else :
      
        id_lph_admin = request.POST.get("id_lph_admin",'')
        nama_auditor = request.POST["nama_auditor"]
        jabatan = request.POST["jabatan"]

        nomor_telepon = request.POST["nomor_telepon"]
        username   = (request.POST.get("username") or "").strip()
        email      = (request.POST.get("email") or "").strip()
        group_val  = 'auditor'
        password   = request.POST.get("password") or ""
        # tanggal_dibuat = request.POST["tanggal_dibuat"]
        
        auditorobj = models.LPHAuditor.objects.filter(nama_auditor=nama_auditor,username=username)
       

        if User.objects.filter(username=username,groups__name = group_val).exists():
            messages.error(request, "Username sudah ada!")
            return render(request, "auditor/create_auditor.html", {
                 "prefill": {"username": username, "email": email, "group": group_val}
            })
        if auditorobj.exists():
            messages.error(request, "auditor sudah ada")
            return redirect("create_auditor")
        else:
            
            models.LPHAuditor(
                id_lph_admin=models.LPHAdmin.objects.get(username = id_lph_admin),
                nama_auditor=nama_auditor,
                jabatan=jabatan,
                email=email,
                nomor_telepon=nomor_telepon,
                username=username,
            ).save()
                # --- Resolve objek Group dari input (dukung ID atau nama) ---
            group = None
            if group_val:
                # Coba sebagai ID dulu
                try:
                    group = Group.objects.get(name=group_val)
                except (ValueError, Group.DoesNotExist):
                    # Bukan ID, coba sebagai nama
                    group, _ = Group.objects.get_or_create(name=group_val)
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username, password=password, email=email
                    )
                    if group:
                        user.groups.add(group)

                messages.success(request, "Akun berhasil dibuat. Silakan login. ")
            
            except Exception as e:
                messages.error(request, f"Gagal membuat akun: {e}")
                return render(request, "auditor/create_auditor.html", {
                    "prefill": {"username": username, "email": email, "group": group_val}
                })

            messages.success(request, "Data auditor Berhasil Ditambahkan!")
        return redirect("read_auditor")

@login_required(login_url="login")  
@role_required(['admin'])
def update_auditor(request, id):
    getauditor = models.LPHAuditor.objects.get(id_lph_auditor=id)
    username1 =getauditor.username
    getuser = User.objects.get(username=username1)
    if request.method == 'GET':
        
        tgl1 = getauditor.tanggal_dibuat.strftime('%Y-%m-%d')
        return render(request, 'auditor/update_auditor.html', {
    
            'getauditor': getauditor,
            'getuser': getuser,
            'id': id,
            'tgl1': tgl1,
        })

    else:
        id_lph_admin = request.POST["id_lph_admin"]
        nama_auditor = request.POST["nama_auditor"]
        jabatan = request.POST["jabatan"]
        nomor_telepon = request.POST["nomor_telepon"]
       
        
        username   = (request.POST.get("username") or "").strip()
        email      = (request.POST.get("email") or "").strip()
        password = (request.POST.get("email") or "").strip()
        if models.auditor.objects.filter(nama_auditor=nama_auditor,jabatan=jabatan,nomor_telepon=nomor_telepon).exclude(id_lph_auditor = id).exists() :
            messages.error(request,"auditor sudah ada!")
            return render(request, 'auditor/update_auditor.html')

        getauditor.id_lph_auditor = models.LPHAdmin.objects.get(id_lph_admin=id_lph_admin)
        getauditor.nama_auditor = nama_auditor
        getauditor.jabatan = jabatan
        getauditor.nomor_telepon = nomor_telepon
        # getauditor.public_url = public_url
        getauditor.email = email
        getauditor.username = username
        # getauditor.tanggal_dibuat = tanggal_dibuat

        if User.objects.filter(username__iexact=username,groups__name__iexact = 'auditor').exclude(pk=getuser.id).exists() :
            messages.error(request, "Username sudah ada!")
            return render(request, "auditor/update_auditor.html", {
                 "prefill": {"username": username, "email": email, }
            })
        
        
        getuser.username = username
        getuser.email = email
        if password:                     # hanya kalau diisi
            getuser.set_password(password)   # <-- PENTING: hash password
        # kalau yang diubah adalah user yang sedang login sendiri:
            if request.user.pk == getuser.pk:
            # jaga sesi tetap valid setelah ganti password
                update_session_auth_hash(request, getuser)

        getuser.save()

        getauditor.save()

        messages.success(request, "Data auditor berhasil diperbarui!")
        return redirect('read_auditor')
    
@login_required(login_url="login")
@role_required(['admin'])
def delete_auditor(request,id) :
    getauditor = models.LPHAuditor.objects.get(id_lph_auditor=id)
    username = getauditor.username
    User.objects.filter(username__iexact=username,groups__name__iexact = 'auditor').delete()
    getauditor.delete()
    messages.success(request, "Data berhasil dihapus!")
    return redirect('read_manufaktur')

'''CRUD admin'''
@login_required(login_url="login")
@role_required(['admin'])
def read_admin(request) :
   
    user = request.user
    # is_admin = user.groups.filter(name__iexact='admin').exists()
    adminobj = models.LPHAdmin.objects.all()
    if not adminobj.exists():
        messages.error(request, "Data admin Tidak Ditemukan!")
    return render(request, 'admin/read_admin.html', {'adminobj': adminobj})

@login_required(login_url="login")
@role_required(['admin'])
def create_admin(request):
    # groupobj = Group.objects.all().order_by('name')
    # user = request.user
    # username = user.username
    # is_admin = user.groups.filter(name__iexact='admin').exists()
    if request.method == "GET":
        return render(request, 
                      'admin/create_admin.html',)
    else :
      
        
        nama_admin = request.POST["nama_admin"]
        kantor = request.POST["kantor"]

        
        username   = (request.POST.get("username") or "").strip()
        email      = (request.POST.get("email") or "").strip()
        group_val  = 'admin'
        password   = request.POST.get("password") or ""
        # tanggal_dibuat = request.POST["tanggal_dibuat"]
        
        adminobj = models.LPHAdmin.objects.filter(nama_admin=nama_admin,username=username)
       

        if User.objects.filter(username=username,groups__name = group_val).exists():
            messages.error(request, "Username sudah ada!")
            return render(request, "admin/create_admin.html", {
                 "prefill": {"username": username, "email": email, "group": group_val}
            })
        if adminobj.exists():
            messages.error(request, "admin sudah ada")
            return redirect("create_admin")
        else:
            
            models.LPHAdmin(

                nama_admin=nama_admin,
                kantor=kantor,
                email=email,

                username=username,
            ).save()
                # --- Resolve objek Group dari input (dukung ID atau nama) ---
            group = None
            if group_val:
                # Coba sebagai ID dulu
                try:
                    group = Group.objects.get(name=group_val)
                except (ValueError, Group.DoesNotExist):
                    # Bukan ID, coba sebagai nama
                    group, _ = Group.objects.get_or_create(name=group_val)
            try:
                
                with transaction.atomic():
                    user = User.objects.create_superuser(
                        username=username, password=password, email=email
                    )
                    if group:
                        user.groups.add(group)

                messages.success(request, "Akun berhasil dibuat. Silakan login. ")
            
            except Exception as e:
                messages.error(request, f"Gagal membuat akun: {e}")
                return render(request, "admin/create_admin.html", {
                    "prefill": {"username": username, "email": email, "group": group_val}
                })

            messages.success(request, "Data admin Berhasil Ditambahkan!")
        return redirect("read_admin")


@login_required(login_url="login")
@role_required(['admin'])
def update_admin(request, id):
    getadmin = models.LPHAdmin.objects.get(id_lph_admin=id)
    username1 =getadmin.username
    print('username', username1)
    getuser = User.objects.get(username=username1)
    print('getuser', getuser)
    if request.method == 'GET':
       
        tgl1 = getadmin.tanggal_dibuat.strftime('%Y-%m-%d')
        return render(request, 'admin/update_admin.html', {
        
            'getadmin': getadmin,
            'getuser': getuser,
            'id': id,
            'tgl1': tgl1,
        })

    else:
 
        nama_admin = request.POST["nama_admin"]
        kantor = request.POST["kantor"]
        # nomor_telepon = request.POST["nomor_telepon"]
       
        
        username   = (request.POST.get("username") or "").strip()
        email      = (request.POST.get("email") or "").strip()
        password = (request.POST.get("password") or "").strip()
        if models.LPHAdmin.objects.filter(nama_admin=nama_admin,kantor=kantor).exclude(id_lph_admin = id).exists() :
            messages.error(request,"admin sudah ada!")
            return render(request, 'admin/update_admin.html')

       
        getadmin.nama_admin = nama_admin
        getadmin.kantor = kantor
   
        # getadmin.public_url = public_url
        getadmin.email = email
        getadmin.username = username
        # getadmin.tanggal_dibuat = tanggal_dibuat

        print('username',username)
        print('email',email)
        print('password',password)
        if User.objects.filter(username__iexact=username,groups__name__iexact = 'admin').exclude(pk=getuser.id).exists() :
            messages.error(request, "Username sudah ada!")
            return render(request, "admin/update_admin.html", {
                 "prefill": {"username": username, "email": email, }
            })
        
        # if password == "" :
        getuser.username = username
        getuser.email = email
        # else :
        if password:                     # hanya kalau diisi
            getuser.set_password(password)   # <-- PENTING: hash password
        # kalau yang diubah adalah user yang sedang login sendiri:
            if request.user.pk == getuser.pk:
            # jaga sesi tetap valid setelah ganti password
                update_session_auth_hash(request, getuser)


        getuser.save()

        getadmin.save()

        messages.success(request, "Data admin berhasil diperbarui!")
        return redirect('read_admin')
    
@login_required(login_url="login")
@role_required(['admin'])
def delete_admin(request,id) :
    
    getadmin = models.LPHAdmin.objects.get(id_lph_admin=id)
    username = getadmin.username
    User.objects.filter(username__iexact=username,groups__name__iexact = 'admin').delete()
    getadmin.delete()
    messages.success(request, "Data berhasil dihapus!")
    return redirect('read_admin')

'''CRUD Supplier'''
@login_required(login_url="login")
@role_required(['admin','auditor','manufaktur'])
def read_supplier(request) :
   
    user = request.user
    # is_supplier = user.groups.filter(name__iexact='supplier').exists()
    supplierobj = models.Supplier.objects.all()
    if not supplierobj.exists():
        messages.error(request, "Data supplier Tidak Ditemukan!")
    return render(request, 'supplier/read_supplier.html', {'supplierobj': supplierobj})

@login_required(login_url="login")
@role_required(['auditor','manufaktur'])
def create_supplier(request):
    # groupobj = Group.objects.all().order_by('name')
    user = request.user
    username = user.username
    is_admin = user.groups.filter(name__iexact='admin').exists()
    is_auditor = user.groups.filter(name__iexact='auditor').exists()
    manufakturobj = models.Manufaktur.objects.all()
    if request.method == "GET":
        return render(request, 
                      'supplier/create_supplier.html',{
                          'is_admin' : is_admin,
                          'is_auditor' : is_auditor,
                          'manufakturobj' : manufakturobj,
                      })
    else :
      
        
        id_manufaktur = request.POST["id_manufaktur"]
        nama_supplier = request.POST["nama_supplier"]
        jenis_bahanbaku = request.POST["jenis_bahanbaku"]
        asal_bahan = request.POST["asal_bahan"]
        status_halal = request.POST["status_halal"]
        if status_halal == 'True' :
            status_halal = True
        else :
            status_halal = False
        supplierobj = models.Supplier.objects.filter(nama_supplier=nama_supplier,jenis_bahanbaku=jenis_bahanbaku)
       

        if supplierobj.exists():
            messages.error(request, "Supplier sudah ada")
            return redirect("create_supplier")
        else:
            
            models.Supplier(

                id_manufaktur=models.Manufaktur.objects.get(username = id_manufaktur),
                nama_supplier=nama_supplier,
                jenis_bahanbaku=jenis_bahanbaku,
                asal_bahan=asal_bahan,
                status_halal=status_halal,
            ).save()
        
          
            messages.success(request, "Data supplier Berhasil Ditambahkan!")
        return redirect("read_supplier")


@login_required(login_url="login")
@role_required(['auditor','manufaktur'])
def update_supplier(request, id):
    getsupplier = models.Supplier.objects.get(id_supplier=id)
    # getauditor = models.LPHAuditor.objects.all()
    manufakturobj = models.Manufaktur.objects.all()
    user = request.user
    username = user.username
    is_admin = user.groups.filter(name__iexact='admin').exists()
    is_auditor = user.groups.filter(name__iexact='auditor').exists()
    if request.method == 'GET':
       
        return render(request, 'supplier/update_supplier.html', {
        
            'getsupplier': getsupplier,
            'manufakturobj': manufakturobj,
            'is_admin': is_admin,
            'is_auditor': is_auditor,
            # 'getauditor': getauditor,
            'id': id,
        })

    else:
 
        id_manufaktur = request.POST["id_manufaktur"]
        nama_supplier = request.POST["nama_supplier"]
        jenis_bahanbaku = request.POST["jenis_bahanbaku"]
        asal_bahan = request.POST["asal_bahan"]
        status_halal = request.POST["status_halal"]
        if status_halal == 'True' :
            status_halal = True
        else :
            status_halal = False
        if models.Supplier.objects.filter(nama_supplier=nama_supplier,jenis_bahanbaku=jenis_bahanbaku).exclude(id_supplier = id).exists() :
            messages.error(request,"supplier sudah ada!")
            return render(request, 'supplier/update_supplier.html')

       
        getsupplier.id_manufaktur = models.Manufaktur.objects.get(username = id_manufaktur)
        getsupplier.nama_supplier = nama_supplier
        getsupplier.jenis_bahanbaku = jenis_bahanbaku
        getsupplier.asal_bahan = asal_bahan
        getsupplier.status_halal = status_halal
        getsupplier.save()
        messages.success(request, "Data supplier berhasil diperbarui!")
        return redirect('read_supplier')
    
@login_required(login_url="login") 
@role_required(['auditor','manufaktur'])
def update_status3(request,id) :
    getsupplier = models.Supplier.objects.get(id_supplier = id)
    if getsupplier.status_halal == True :
        getsupplier.status_halal = False
    else :
        getsupplier.status_halal = False
    getsupplier.save()
    return redirect('read_supplier')

@login_required(login_url="login")
@role_required(['auditor','manufaktur'])
def delete_supplier(request,id) :
    getsupplier = models.Supplier.objects.get(id_supplier=id)
    getsupplier.delete()
    messages.success(request, "Data berhasil dihapus!")
    return redirect('read_supplier')

'''CRUD produk'''
@login_required(login_url="login")
@role_required(['admin','auditor','manufaktur'])
def read_produk(request) :
   
    # user = request.user
    # is_produk = user.groups.filter(name__iexact='produk').exists()
    produkobj = models.Produk.objects.all()
    if not produkobj.exists():
        messages.error(request, "Data produk Tidak Ditemukan!")
    return render(request, 'produk/read_produk.html', {'produkobj': produkobj})

@login_required(login_url="login")
@role_required(['manufaktur'])
@transaction.atomic
def create_produk(request):
    user = request.user
    is_manufaktur = user.groups.filter(name__iexact='manufaktur').exists()
    manufakturobj = models.Manufaktur.objects.all()

    if request.method == "GET":
        return render(request, 'produk/create_produk.html', {
            'is_manufaktur': is_manufaktur,
            'manufakturobj': manufakturobj,
        })

    # POST
    id_manufaktur = request.POST["id_manufaktur"]          # ini username manufaktur (sesuai kodenmu)
    nama_produk    = request.POST["nama_produk"].strip()
    status_analisis = request.POST["status_analisis"].strip()

    # cek duplikat (pakai relasi username)
    produkobj = models.Produk.objects.filter(
        nama_produk__iexact=nama_produk,
        id_manufaktur__username=id_manufaktur
    )
    if produkobj.exists():
        messages.error(request, "Produk sudah ada")
        return redirect("create_produk")

    # ambil objek manufaktur
    manuf = models.Manufaktur.objects.get(username=id_manufaktur)

    # simpan Produk dulu supaya dapat id_produk
    produk = models.Produk(
        id_manufaktur=manuf,
        nama_produk=nama_produk,
        status_analisis=status_analisis,
    )
    produk.save()

    # generate QR dari id_produk (kalau mau, boleh ganti payload)
    id_produk = produk.id_produk
    png_bytes = make_qr_png_bytes(id_produk)

    # upload BYTES ke Supabase Storage --> dapat public URL
    try:
        public_url = upload_bytes_and_get_url(
            content=png_bytes,
            filename=f"{id_produk}.png",
            folder="qr"  # folder di bucket
        )
    except Exception as e:
        # batalkan transaksi supaya tidak ada Produk setengah jadi
        transaction.set_rollback(True)
        messages.error(request, f"Gagal upload file: {e}")
        return redirect("create_produk")

    # simpan URL ke field qr_code
    produk.qr_code = public_url
    produk.save(update_fields=["qr_code"])

    messages.success(request, "Data produk Berhasil Ditambahkan!")
    return redirect("read_produk")


@login_required(login_url="login")
@role_required(['auditor','manufaktur'])
def update_produk(request, id):
    getproduk = models.Produk.objects.get(id_produk=id)
    # getauditor = models.LPHAuditor.objects.all()
    manufakturobj = models.Manufaktur.objects.all()
    user = request.user
    username = user.username
    is_manufaktur = user.groups.filter(name__iexact='manufaktur').exists()
    if request.method == 'GET':
       
        return render(request, 'produk/update_produk.html', {
        
            'getproduk': getproduk,
            'manufakturobj': manufakturobj,
            'is_manufaktur': is_manufaktur,
            # 'getauditor': getauditor,
            'id': id,
        })

    else:
 
        id_manufaktur = request.POST["id_manufaktur"]
        nama_produk = request.POST["nama_produk"]
        status_analisis = request.POST["status_analisis"]
        if models.Produk.objects.filter(nama_produk=nama_produk,id_manufaktur__username=id_manufaktur).exclude(id_produk = id).exists() :
            messages.error(request,"Produk sudah ada!")
            return render(request, 'produk/update_produk.html')

       
        getproduk.id_manufaktur = models.Manufaktur.objects.get(username = id_manufaktur)
        getproduk.nama_produk = nama_produk
        getproduk.status_analisis = status_analisis

        getproduk.save()
        messages.success(request, "Data produk berhasil diperbarui!")
        return redirect('read_produk')

@login_required(login_url="login")
@role_required(['manufaktur'])
def delete_produk(request,id) :
    getproduk = models.Produk.objects.get(id_produk=id)
    url = getproduk.qr_code
    if url == '' or url == None :
        pass 
    else :
        delete_file_by_public_url(url)
    getproduk.delete()
    messages.success(request, "Data berhasil dihapus!")
    return redirect('read_produk')


@login_required(login_url="login")
@role_required(['admin','auditor','manufaktur'])
def read_produk_supplier(request) : 
    user = request.user
    username = user.username
    manufaktur = request.GET.get('manufaktur','')
    is_manufaktur = user.groups.filter(name__iexact='manufaktur').exists()
    if manufaktur != '' :
        # tanggal_mulai = tgl.strftime('%d/%m/%Y')
        # tanggal_akhir = tgl2.strftime('%d/%m/%Y')
        print('tes')
        print('manufaktur',manufaktur)
        allproduk_supplier = models.ProdukSupplier.objects.filter(id_produk__id_manufaktur__username =manufaktur)
    elif is_manufaktur :
        print('tes2')
        allproduk_supplier = models.ProdukSupplier.objects.filter(id_produk__id_manufaktur__username =username)
        # tanggal_mulai = tgl
        # tanggal_akhir = tgl2
    else :
        allproduk_supplier = models.ProdukSupplier.objects.all()
    print('TES' ,allproduk_supplier)
    manufakturobj = models.Manufaktur.objects.all()
    list1 = []
    for item in allproduk_supplier:
        list2 = []
        produk_supplierobj = models.DetailProdukSupplier.objects.filter(id_produk_supplier = item.id_produk_supplier)
        if not produk_supplierobj.exists() :
            get_produk_supplier = models.ProdukSupplier.objects.get(id_produk_supplier =item.id_produk_supplier )
            get_produk_supplier.delete()
            continue

        list2.append(item)
        list2.append(produk_supplierobj)
        
        list1.append(list2)
    print('list1 : ',list1)
    return render(request, "produk_supplier/read_produk_supplier.html",{
        "produk_supplierobj" : list1,  
        'manufakturobj' : manufakturobj,
        'manufaktur' : manufaktur ,
    })

@login_required(login_url="login")
@role_required(['manufaktur'])
def create_produk_supplier(request) :
    user = request.user
    username = user.username
    is_manufaktur = user.groups.filter(name__iexact='manufaktur').exists()
    if is_manufaktur :
        produkobj = models.Produk.objects.filter(id_manufaktur__username = username)
        supplierobj = models.Supplier.objects.filter(id_manufaktur__username= username)
    else :
        produkobj = models.Produk.objects.all()
        supplierobj = models.Supplier.objects.all()
    if request.method == 'GET' :
        return render (request, 'produk_supplier/create_produk_supplier.html', {
            'produkobj' : produkobj,
            'supplierobj' : supplierobj,
        })
    
    else :
        id_produk = request.POST['id_produk']
       
        id_supplier = request.POST.getlist('id_supplier')
        peran_supplier = request.POST.getlist('peran_supplier') 
        catatan_rantai_pasok = request.POST.getlist('catatan_rantai_pasok')
       
        produk_supplierobj = models.ProdukSupplier(
            id_produk  = models.Produk.objects.get(
                    id_produk = id_produk),
        )
        produk_supplierobj.save()

    
        for a, b, c in zip (id_supplier, peran_supplier, catatan_rantai_pasok):
            tes = models.DetailProdukSupplier(
                id_produk_supplier = produk_supplierobj,
                id_supplier = models.Supplier.objects.get(
                    id_supplier = a),
                peran_supplier = b,
                catatan_rantai_pasok = c,
            )
            tes.save()

        
            
        messages.success(request, "Data produk supplier berhasil ditambahkan")
        return redirect("read_prodsup")

@login_required(login_url="login") 
@role_required(['auditor','manufaktur'])
def update_produk_supplier(request, id):
    print('id',id)
    detailobj = models.DetailProdukSupplier.objects.get(id_detail_produk_supplier=id)  
    user = request.user
    username = user.username
    is_manufaktur = user.groups.filter(name__iexact='manufaktur').exists()
    if is_manufaktur :
        produkobj = models.Produk.objects.filter(id_manufaktur__username = username)
        supplierobj = models.Supplier.objects.filter(id_manufaktur__username= username)
    else :
        produkobj = models.Produk.objects.all()
        supplierobj = models.Supplier.objects.all()
    if request.method == "GET":
       
        return render(request, "produk_supplier/update_produk_supplier.html", {
            'produkobj': produkobj,
            "detailobj": detailobj,
            "supplierobj": supplierobj,
            "id": id,
          
        })
    else:
        id_produk = request.POST.get('id_produk')
       
        id_supplier = request.POST.get('id_supplier')
        peran_supplier = request.POST.get('peran_supplier') 
        catatan_rantai_pasok = request.POST.get('catatan_rantai_pasok')
       
        
        
        detailobj.id_produk_supplier.id_produk = models.Produk.objects.get(id_produk=id_produk)
        detailobj.id_supplier = models.Supplier.objects.get(id_supplier=id_supplier)
        detailobj.peran_supplier = peran_supplier
        detailobj.catatan_rantai_pasok = catatan_rantai_pasok

        detailobj.id_produk_supplier.save()
        detailobj.save()

        messages.success(request, 'Data produk_supplier  Berhasil Diperbarui!')
        return redirect('read_prodsup')
    
@login_required(login_url="login")
@role_required(['manufaktur'])
def delete_produk_supplier(request, id) :
    getdetailobj = models.DetailProdukSupplier.objects.get(id_detail_produk_supplier = id)
   
    getdetailobj.delete()

    messages.error(request, "Data produk_supplier berhasil dihapus!")
    return redirect('read_prodsup')


def dashboard(request) :

    filterumkm_halal = models.ProdukSupplier.objects.filter(id_produk__id_manufaktur__status_halal = True)
    filterumkm_nonhalal = models.ProdukSupplier.objects.filter(id_produk__id_manufaktur__status_halal = False)

    
    jumlah_halal = 0
    jumlah_nonhalal = 0
    minimal = 0.5
    for item in filterumkm_halal :

        id_prodsup = item.id_produk_supplier

        supp_halal = models.DetailProdukSupplier.objects.filter(id_produk_supplier = id_prodsup,id_supplier__status_halal=True).count()

        total_sup =  models.DetailProdukSupplier.objects.filter(id_produk_supplier = id_prodsup).count()
        
        
        aktual = supp_halal/total_sup
        
        if aktual >= minimal :
            jumlah_halal +=1
        
        else :
            jumlah_nonhalal +=1
    
    return render(request,'base/dashboard.html',{
        'halal' : jumlah_halal,
        'nonhalal' : jumlah_nonhalal
    })

