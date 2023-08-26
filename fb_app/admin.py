from django.contrib import admin

from assignment6.models import Group, Membership, GroupAdmin
# Register your models here.

admin.site.register(Group)
admin.site.register(Membership)
admin.site.register(GroupAdmin)