def auditor(request):
    return{'auditor' : request.user.groups.filter(name='auditor').exists()}

def admin(request):
    return{'admin' : request.user.groups.filter(name='admin').exists()}

def manufaktur(request):
    return{'manufaktur' : request.user.groups.filter(name='manufaktur').exists()}


