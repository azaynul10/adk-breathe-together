from google.cloud.monitoring_v3 import MetricServiceClient
from google.api import metric_pb2 as MetricDescriptor
import os

def create_custom_metrics():
    # Set project ID
    project_id = "my-aqms-project"
    
    # Create client
    client = MetricServiceClient()
    project_name = f"projects/{project_id}"
    
    # Define PM2.5 metric descriptor
    pm25_descriptor = MetricDescriptor.MetricDescriptor()
    pm25_descriptor.type = "custom.googleapis.com/pm25_level"
    pm25_descriptor.metric_kind = MetricDescriptor.MetricDescriptor.MetricKind.GAUGE
    pm25_descriptor.value_type = MetricDescriptor.MetricDescriptor.ValueType.DOUBLE
    pm25_descriptor.unit = "ug/m3"
    pm25_descriptor.description = "PM2.5 concentration level"
    pm25_descriptor.display_name = "PM2.5 Level"
    
    # Create the metric descriptor
    try:
        descriptor = client.create_metric_descriptor(
            name=project_name, 
            metric_descriptor=pm25_descriptor
        )
        print(f"Created metric descriptor: {descriptor.name}")
    except Exception as e:
        print(f"Error creating metric: {e}")

if __name__ == "__main__":
    create_custom_metrics()