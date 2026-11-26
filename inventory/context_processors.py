from .models import Category

DEFAULT_CATEGORIES = [
    ('lips', 'Lips', '💄', 'Lipsticks, tints, glosses, and balms'),
    ('face', 'Face', '✨', 'Foundations, powders, blush, and concealers'),
    ('eyes', 'Eyes', '👁️', 'Eyeliners, mascaras, and eyeshadows'),
    ('bath_and_body', 'Bath and Body', '🧴', 'Body wash, scrubs, lotions, and soaps'),
    ('fragrance', 'Fragrance', '🌸', 'Body mists, colognes, and perfumes'),
]


def categories_processor(request):
    try:
        categories = Category.objects.all().order_by('name')
    except Exception:
        categories = []

    return {
        'all_categories': categories,
    }
