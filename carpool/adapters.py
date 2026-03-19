from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return
        email = sociallogin.account.extra_data.get('email', '')
        username = email.split('@')[0]
        sociallogin.user.username = username
        sociallogin.user.role = 'passenger'

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if not user.role:
            user.role = 'passenger'
            user.save()
        return user

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.role = 'passenger'
        email = data.get('email', '')
        if not user.username:
            user.username = email.split('@')[0]
        return user