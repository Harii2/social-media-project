from .models import User, Post, Comment, Reaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Sum, Avg, Min, Max, Count, Case, When, IntegerField, F, Q
import datetime


class InvalidUserException(Exception):
    def __init__(self, user_id):
        self.user_id = user_id

    def __str__(self):
        return f'Invalid user with id {self.user_id}'


class InvalidPostException(Exception):
    def __init__(self, post_id):
        self.post_id = post_id

    def __str__(self):
        return f'Invalid post with id {self.post_id}'


class InvalidCommentException(Exception):
    def __init__(self, comment_id):
        self.comment_id = comment_id

    def __str__(self):
        return f'Invalid comment with id {self.comment_id}'


class InvalidPostContent(Exception):
    def __str__(self):
        return "Post content not to be empty."


class InvalidCommentContent(Exception):
    def __str__(self):
        return "Comment content not to be empty"


class InvalidReplyContent(Exception):
    def __str__(self):
        return "Reply not to be Empty"


class UserCannotDeletePostException(Exception):
    def __str__(self):
        return "user cannot be delete another ones post"


class InvalidReactionTypeException(Exception):
    def __str__(self):
        return "Invalid Reaction type Exception"


def get_user_by_id(user_id):
    try:
        user = User.objects.get(id=user_id)
        return user
    except ObjectDoesNotExist:
        raise InvalidUserException(user_id)


def get_post_by_id(post_id):
    try:
        post = Post.objects.get(id=post_id)
        return post
    except ObjectDoesNotExist:
        raise InvalidPostException(post_id)


def get_comment_by_id(comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
        return comment
    except ObjectDoesNotExist:
        raise InvalidCommentException(comment_id)


def create_post(user_id, post_content):
    user = get_user_by_id(user_id)
    if post_content.strip() == "":
        raise InvalidPostContent("Post content cant be empty")

    post = Post.objects.create(content=post_content, posted_by=user)
    return post.id


def create_comment(user_id, post_id, comment_content):
    user = get_user_by_id(user_id)
    post = get_post_by_id(post_id)
    if comment_content.strip() == "":
        raise InvalidCommentContent("Comment Content not to be empty")

    comment = Comment.objects.create(content=comment_content, commented_by=user, post=post)
    return comment.id


def get_original_comment(comment):
    while comment.parent_comment:
        comment = comment.parent_comment
    return comment


def reply_to_comment(user_id, comment_id, reply_content):
    user = get_user_by_id(user_id)
    comment = get_comment_by_id(comment_id)

    if reply_content.strip() == "":
        raise InvalidReplyContent("Reply cannot be empty")

    parent_comment = get_original_comment(comment)

    reply_comment = Comment.objects.create(content=reply_content, commented_by=user, post=parent_comment.post,
                                           parent_comment=parent_comment)
    return reply_comment.id


def react_to_post(user_id, post_id, reaction_type):
    user = get_user_by_id(user_id)
    post = get_post_by_id(post_id)
    REACTION_CHOICES = [
        'WOW',
        'LIT',
        'LOVE',
        'HAHA',
        'THUMBS-UP',
        'THUMBS-DOWN',
        'ANGRY',
        'SAD',
    ]

    if reaction_type not in REACTION_CHOICES:
        raise InvalidReactionTypeException(reaction_type)

    is_already_reacted_to_post = Reaction.objects.filter(reacted_by=user, post=post)
    if is_already_reacted_to_post:
        is_already_reacted_to_post = is_already_reacted_to_post[0]
        if is_already_reacted_to_post.reaction == reaction_type:
            is_already_reacted_to_post.delete()
            return f"Previous Reaction {reaction_type} Deleted Succesfully"
        else:
            prev_reaction = is_already_reacted_to_post.reaction
            is_already_reacted_to_post.reaction = reaction_type
            is_already_reacted_to_post.reacted_at = datetime.datetime.now()
            is_already_reacted_to_post.save()
            return f"Your reaction from {prev_reaction} to {reaction_type} updated succesfully "

    reaction = Reaction(reaction=reaction_type, reacted_by=user, post=post)
    reaction.save()
    return reaction.id


def react_to_comment(user_id, comment_id, reaction_type):
    user = get_user_by_id(user_id)
    comment = get_comment_by_id(comment_id)
    REACTION_CHOICES = [
        'WOW',
        'LIT',
        'LOVE',
        'HAHA',
        'THUMBS-UP',
        'THUMBS-DOWN',
        'ANGRY',
        'SAD',
    ]
    if reaction_type not in REACTION_CHOICES:
        raise InvalidReactionTypeException(reaction_type)

    is_already_reacted_to_comment = Reaction.objects.filter(reacted_by=user, comment=comment)

    if is_already_reacted_to_comment:
        is_already_reacted_to_comment = is_already_reacted_to_comment[0]
        if is_already_reacted_to_comment.reaction == reaction_type:
            is_already_reacted_to_comment.delete()
            return f"Your reaction {reaction_type} to comment is deleted"
        else:
            prev_reaction = is_already_reacted_to_comment.reaction
            is_already_reacted_to_comment.reaction = reaction_type
            is_already_reacted_to_comment.save()
            is_already_reacted_to_comment.reacted_at = datetime.datetime.now()
            is_already_reacted_to_comment.save()
            return f"Your reaction from {prev_reaction} to {reaction_type} updated succesfully"

    reaction = Reaction(reaction=reaction_type, reacted_by=user, comment=comment)
    reaction.save()
    return reaction.id


def get_total_reaction_count():
    total_reaction_count = Reaction.objects.aggregate(count=Count('id'))
    return total_reaction_count


def get_reaction_metrics(post_id):
    post = get_post_by_id(post_id)
    metrics_query = list(Reaction.objects.filter(post=post).values_list('reaction').annotate(count=Count('reaction')))
    metric = dict()
    for reaction, count in metrics_query:
        metric[reaction] = count
    return metric


def delete_post(user_id, post_id):
    user = get_user_by_id(user_id)
    post = get_post_by_id(post_id)

    if post.user != user:
        raise UserCannotDeletePostException("User cannot delete another ones post")

    post.delete()
    return "Deleted Succesfully"


# 10
def get_posts_with_more_positive_reactions():
    positive = ["THUMBS-UP", "LIT", "LOVE", "HAHA", "WOW"]
    negative = ["SAD", "ANGRY", "THUMBS-DOWN"]
    posts_with_more_positive_reactions = list(Reaction.objects.values_list('post__id').annotate(
        pos=Count(Case(When(reaction__in=positive, then=1), output_field=IntegerField())),
        neg=Count(Case(When(reaction__in=negative, then=1), output_field=IntegerField()))).filter(pos__gt=F('neg')))

    posts_id = []
    for post in posts_with_more_positive_reactions:
        posts_id.append(post[0])
    return posts_id


# 11
def get_posts_reacted_by_user(user_id):
    user = get_user_by_id(user_id)
    post_ids = list(Reaction.objects.values_list('post').filter(user=user))
    return post_ids


def get_user_object_by_id(user):
    # user = get_user_by_id(user_id)
    user_obj = {
        "user_id": user.id,
        "name": user.name,
        "profile_pic": user.profile_pic
    }
    return user_obj


# 12
def get_reactions_to_post(post_id):
    post = get_post_by_id(post_id)
    reaction_list = list(Reaction.objects.values_list(
        'reacted_by', 'reacted_by__name', 'reacted_by__profile_pic', 'reaction'
    ).filter(post=post))
    reactions = []
    for reaction in reaction_list:
        obj = dict()
        obj['user_id'] = reaction[0]
        obj['name'] = reaction[1]
        obj['profile_pic'] = reaction[2]
        obj['reaction'] = reaction[3]
        reactions.append(obj)
    return reactions


def get_reactions_for_post_by_post_object(post):
    total_reactions_for_post = Reaction.objects.filter(post=post).aggregate(count=Count('id'))
    unique_reactions = list(Reaction.objects.values_list('reaction').filter(post=post).distinct())
    reactions = []
    for reaction in unique_reactions:
        reactions.append(reaction[0])

    total_reactions_for_post["reactions"] = reactions
    return total_reactions_for_post


def get_reactions_for_comment_by_comment_object(comment):
    total_reactions_for_post = Reaction.objects.filter(comment=comment).aggregate(count=Count('id'))
    unique_reactions = list(Reaction.objects.values_list('reaction').filter(comment=comment).distinct())
    reactions = []
    for reaction in unique_reactions:
        reactions.append(reaction[0])

    total_reactions_for_post["reactions"] = reactions
    return total_reactions_for_post


def get_reactions_for_replies_by_reply_object(reply_object):
    total_reactions_for_replies = Reaction.objects.filter(comment=reply_object).aggregate(count=Count('id'))
    unique_reactions = list(Reaction.objects.values_list('reaction').filter(comment=reply_object).distinct())
    reactions = []
    for reaction in unique_reactions:
        reactions.append(reaction[0])

    total_reactions_for_replies["reactions"] = reactions
    return total_reactions_for_replies


def get_replies_for_the_comment_by_comment_object(comment):
    query = list(Comment.objects.filter(parent_comment=comment))
    replies = []
    for reply in query:
        reply_obj = dict()
        reply_obj['commented_id'] = reply.commented_by.id
        reply_obj['commenter'] = get_user_object_by_id(reply.commented_by)
        reply_obj['commented_at'] = reply.commented_at
        reply_obj['comment_content'] = reply.content
        reply_obj['reactions'] = get_reactions_for_replies_by_reply_object(reply)
        replies.append(reply_obj)
    return replies


def get_comments_for_post_by_post_object(post):
    comments = []
    query = list(Comment.objects.filter(post=post, parent_comment=None))
    for comment in query:
        comment_obj = dict()
        comment_obj['commented_id'] = comment.commented_by.id
        comment_obj['commenter'] = get_user_object_by_id(comment.commented_by)
        comment_obj['commented_at'] = comment.commented_at
        comment_obj['comment_content'] = comment.content
        comment_obj['reactions'] = get_reactions_for_comment_by_comment_object(comment)
        comment_obj['replies'] = get_replies_for_the_comment_by_comment_object(comment)
        comments.append(comment_obj)
    return comments



def get_group_object_by_post_objects(post):
    group_obj = dict()
    if post.group:
        group_obj["group_id"] = post.group.id
        group_obj["group_name"] = post.group.name
        return group_obj
    return "None"

#13
def get_post(post_id):
    post = get_post_by_id(post_id)
    post_obj = dict()
    post_obj["post_id"] = post.id
    post_obj["group"] = get_group_object_by_post_objects(post)
    post_obj['posted_by'] = get_user_object_by_id(post.posted_by)
    post_obj['posted_at'] = post.posted_at
    post_obj['post_content'] = post.content
    post_obj['reactions'] = get_reactions_for_post_by_post_object(post)
    post_obj['comments'] = get_comments_for_post_by_post_object(post)
    return post_obj


#14
def get_user_posts(user_id):
    user = get_user_by_id(user_id)
    posts = list(Post.objects.values_list('id').filter(posted_by=user))
    # print(posts)
    user_posts = []
    for post_id in posts:
        user_posts.append(get_post(post_id[0]))
    return user_posts


def get_replies_for_comment(comment_id):
    comment = get_comment_by_id(comment_id)
    return get_replies_for_the_comment_by_comment_object(comment)