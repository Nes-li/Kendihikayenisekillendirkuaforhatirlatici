def theme(request):
    """
    Kullanıcının seçtiği temayı (light/dark) şablonlara ileten context processor.
    Varsayılan tema: 'light'
    """
    return {
        'current_theme': request.session.get('theme', 'light')
    }
