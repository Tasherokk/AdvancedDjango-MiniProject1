from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .tasks import generate_report_task
from .models import AnalyticsReport
from .serializers import AnalyticsReportSerializer
from django.http import FileResponse
import os

class GenerateReportView(APIView):
    """
    POST -> trigger Celery task to generate a CSV report
    """
    permission_classes = [permissions.IsAdminUser]  # only Admin can generate

    def post(self, request):
        report_type = request.data.get('report_type', 'csv')
        task_result = generate_report_task.delay(report_type=report_type)
        return Response({
            "detail": "Report generation started.",
            "task_id": task_result.id
        }, status=status.HTTP_202_ACCEPTED)

class DownloadReportView(APIView):
    """
    GET -> download the generated CSV report from media/reports
    (If we have persisted the path or store the file in AnalyticsReport).
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, report_id):
        # If you're storing in the DB:
        report_obj = AnalyticsReport.objects.filter(id=report_id).first()
        if not report_obj or not report_obj.file:
            return Response({"detail": "Report not found or not generated."}, status=404)

        file_path = report_obj.file.path
        if not os.path.exists(file_path):
            return Response({"detail": "Report file missing."}, status=404)

        # Serve the file
        file_handle = open(file_path, 'rb')
        response = FileResponse(file_handle, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
