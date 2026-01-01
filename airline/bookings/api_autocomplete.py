from django.http import JsonResponse
from .models import Flight

def city_suggestions(request):
    query = request.GET.get('q', '').strip()
    field = request.GET.get('field', 'origin')
    show_all = request.GET.get('all', 'false') == 'true'
    
    if show_all or len(query) == 0:
        # Show all available cities when requested or field is empty
        if field == 'origin':
            cities = Flight.objects.filter(
                is_active=True
            ).values_list('origin', flat=True).distinct().order_by('origin')[:20]
        else:
            cities = Flight.objects.filter(
                is_active=True
            ).values_list('destination', flat=True).distinct().order_by('destination')[:20]
    elif len(query) < 2:
        return JsonResponse({'suggestions': []})
    else:
        # Filter by query
        if field == 'origin':
            cities = Flight.objects.filter(
                origin__icontains=query,
                is_active=True
            ).values_list('origin', flat=True).distinct()[:10]
        else:
            cities = Flight.objects.filter(
                destination__icontains=query,
                is_active=True
            ).values_list('destination', flat=True).distinct()[:10]
    
    return JsonResponse({'suggestions': list(cities)})