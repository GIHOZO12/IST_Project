from django.urls import path

from .views import *


urlpatterns=[
    path('purchase-request/',PurchaseRequestView.as_view(), name="purchase-request"),
    path('Get-purchase-request/',PurchaseRequestListView.as_view(), name="Get-purchase-request"),
    path('Get-purchase-request/<int:id>/', PurchaseRequestByIdView.as_view(), name="Get-purchase-request-by-id"),
    path('update-purchase-request/<int:id>/',UpdatePurchaseRequestView.as_view(), name="update-purchase-request"),
    path('approve-request/<int:id>/',ApproveRequestView.as_view(), name="approve-request"),
    path('reject-request/<int:id>/',RejectRequestView.as_view(), name="reject-request"),
    path('submit-receipt/<int:id>/', SubmitReceiptView.as_view(), name="submit-receipt"),
    path('download/<str:file_type>/<int:file_id>/', DownloadFileView.as_view(), name="download-file"),
]
