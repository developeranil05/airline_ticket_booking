from django.shortcuts import render

def test_monitoring(request):
    return render(request, 'monitoring/test_new.html')