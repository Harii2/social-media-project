from assignment6.utils import get_user_by_id, InvalidPostContent, get_post
from django.core.exceptions import ObjectDoesNotExist
from .exceptions import InvalidGroupNameException, InvalidMemberException, InvalidGroupException, \
    UserNotInGroupException, UserIsNotAdminException, InvalidOffSetValueException, InvalidLimitSetValueException

from assignment6.models import Group, Membership, GroupAdmin, User, Post, Comment, Reaction
from django.db.models import Sum, Avg, Min, Max, Count, Case, When, IntegerField, F


def get_user_for_membership_in_group_by_id(user_id):
    try:
        user = User.objects.get(id=user_id)
        return user
    except ObjectDoesNotExist:
        raise InvalidMemberException(user_id)


def get_group_by_group_id(group_id):
    try:
        group = Group.objects.get(id=group_id)
        return group
    except ObjectDoesNotExist:
        raise InvalidGroupException(group_id)


def is_user_in_group(user, group):
    is_memeber = Membership.objects.filter(group=group, member=user)
    if not is_memeber:
        raise UserNotInGroupException(user.id)
    return


def is_user_is_admin_to_group(user, group):
    is_admin = GroupAdmin.objects.filter(admin=user, group=group)
    if not is_admin:
        raise UserIsNotAdminException(user.id)
    return


def create_group(user_id, name, member_ids):
    group_admin = get_user_by_id(user_id)
    if name == "":
        raise InvalidGroupNameException("Name Not to be empty")

    members = User.objects.filter(id__in=member_ids)

    for user in members:
        member_ids.remove(user.id)

    for user_id in member_ids:
        raise InvalidMemberException(user_id)

    group = Group.objects.create(name=name)
    Membership.objects.create(group=group, member=group_admin, membership_type=Membership.ADMIN, is_admin=True)
    Membership.objects.bulk_create([Membership(group=group, member=member) for member in members])
    GroupAdmin.objects.create(group=group, admin=group_admin)
    return group.id


def add_member_to_group(user_id, new_member_id, group_id):
    user = get_user_by_id(user_id)
    new_member_user = get_user_for_membership_in_group_by_id(new_member_id)
    group = get_group_by_group_id(group_id)
    is_user_in_group(user, group)
    is_user_is_admin_to_group(user, group)

    is_member_already_exists = Membership.objects.filter(group=group, member=new_member_user)
    if not is_member_already_exists:
        Membership.objects.create(group=group, member=new_member_user)
        return "Added succesfully"
    return "User is already in group"


# 4
def remove_member_from_group(user_id, member_id, group_id):
    user = get_user_by_id(user_id)
    member = get_user_for_membership_in_group_by_id(member_id)
    group = get_group_by_group_id(group_id)

    is_user_in_group(user, group)
    is_user_in_group(member, group)
    is_user_is_admin_to_group(user, group)

    member = Membership.objects.filter(group=group, member=member)
    member.delete()
    return 'Removed Succesfully'


# 5
def make_member_as_admin(user_id, member_id, group_id):
    user = get_user_by_id(user_id)
    member = get_user_for_membership_in_group_by_id(member_id)
    group = get_group_by_group_id(group_id)

    is_user_in_group(user, group)
    is_user_in_group(member, group)
    is_user_is_admin_to_group(user, group)

    is_member_already_admin = GroupAdmin.objects.filter(group=group, admin=get_user_by_id(member_id))

    if is_member_already_admin:
        return "Already your are admin to this group"

    member = list(Membership.objects.filter(group=group, member=member))[0]
    member.membership_type = Membership.ADMIN
    member.save()
    group_admin = GroupAdmin.objects.create(group=group, admin=get_user_by_id(member_id))
    return "Updated Succesfully with admin role with id: " + str(group_admin.id)


# 6
def create_post(user_id, post_content, group_id=None):
    user = get_user_by_id(user_id)
    group = get_group_by_group_id(group_id)

    is_user_in_group(user, group)

    if post_content == "":
        raise InvalidPostContent("Not to be empty")

    post = Post.objects.create(content=post_content, posted_by=user, group=group)
    return post.id


# 7
def get_group_feed(user_id, group_id, offset, limit):
    user = get_user_by_id(user_id)
    group = get_group_by_group_id(group_id)
    if offset < 0:
        raise InvalidOffSetValueException("Can't be less than to zero")
    if limit <= 0:
        raise InvalidLimitSetValueException("Can't be less than equals to zero")

    is_user_in_group(user, group)
    group_posts = []
    group_post_ids = list(Post.objects.values('id').filter(group=group).order_by('-posted_by')[offset:offset + limit])
    print(group, group_post_ids)

    for post_id in group_post_ids:
        group_posts.append(get_post(post_id['id']))
    return group_posts


# 8
def get_posts_with_more_comments_than_reactions():
    posts = Post.objects.annotate(comments_count=Count('comments'), reactions_count=Count('reactions')).filter(
        comments_count__gt=F('reactions_count'))
    post_ids = posts.values_list('id', flat=True)
    return list(post_ids)


# 9
def get_user_posts(user_id):
    user = get_user_by_id(user_id)
    posts = list(Post.objects.values('id').filter(posted_by=user_id))
    user_posts = []
    for post_id in posts:
        user_posts.append(get_post(post_id['id']))
    return user_posts


# 10
def get_silent_group_members(group_id):
    group = get_group_by_group_id(group_id)
    group_members = group.members.all()
    users_with_posts = Post.objects.filter(group=group).values('posted_by').distinct()
    silent_members = group_members.exclude(id__in=users_with_posts)
    silent_member_ids = silent_members.values_list('id', flat=True)
    return list(silent_member_ids)


# 11
def get_posts_with_more_comments_than_reactions():
    posts = Post.objects.annotate(
        comment_count=Count('comment', distinct=True),
        reaction_count=Count('reaction')
    ).filter(comment_count__gt=F('reaction_count'))

    post_ids = posts.values_list('id', flat=True)
    return list(post_ids)
