from celery import shared_task
from .models import ProcessingRequest, Product
import requests
from PIL import Image
from io import BytesIO
import uuid
import os

@shared_task(name="process_images_task")
def process_images_task(request_id):
    processing_request = ProcessingRequest.objects.get(request_id=request_id)
    processing_request.status = 'in progress'
    processing_request.save()

    products = Product.objects.filter(processing_request=processing_request)

    for product in products:
        input_urls = product.input_image_urls.split(',')
        output_urls = []

        for url in input_urls:
            response = requests.get(url.strip())
            image = Image.open(BytesIO(response.content))
            output = BytesIO()

            image.save(output, format='JPEG', quality=50)
            output_filename = f"{uuid.uuid4()}.jpg"
            output_path = os.path.join('/path/to/save', output_filename)
            with open(output_path, 'wb') as f:
                f.write(output.getvalue())

            output_urls.append(output_path)

        product.output_image_urls = ','.join(output_urls)
        product.save()

    processing_request.status = 'completed'
    processing_request.save()

    trigger_webhook(request_id)

def trigger_webhook(request_id):
    webhook_url = "http://example.com/webhook"
    payload = {"request_id": request_id, "status": "completed"}
    requests.post(webhook_url, json=payload)

# @shared_task()