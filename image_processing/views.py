from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ProcessingRequest, Product
from .tasks import process_images_task
import csv
from io import StringIO
from rest_framework import status
from django.core.files.storage import default_storage
import uuid

class UploadCSV(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Save the file temporarily
            file_name = default_storage.save(file.name, file)
            file_path = default_storage.path(file_name)

            # Read and validate CSV
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                # if reader.fieldnames != ['S. No.', 'Product Name', 'Input Image Urls']:
                #     return Response({"error": "Invalid CSV headers"}, status=status.HTTP_400_BAD_REQUEST)

                # Validate and queue tasks for each row
                request_id = str(uuid.uuid4())
                for row in reader:
                    serial_number = row['S NO']
                    product_name = row['Product Name']
                    input_image_urls = row['Image Urls'].split(',')
                    if not serial_number or not product_name or not input_image_urls:
                        return Response({"error": "Invalid data in CSV"}, status=status.HTTP_400_BAD_REQUEST)
                    ProcessingRequest.objects.create(request_id=request_id, status="Processing")
                    process_images_task.delay(request_id)
            return Response({"request_id": request_id}, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

class CheckStatus(APIView):
    def get(self, request, request_id):
        try:
            processing_request = ProcessingRequest.objects.get(request_id=request_id)
            return Response({"status": processing_request.status})
        except ProcessingRequest.DoesNotExist:
            return Response({"error": "Invalid request ID"}, status=404)
